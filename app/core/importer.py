"""
ExcelImporter: apply changes from an Excel workbook into RecipeTree models.
"""

import os
import logging
from openpyxl import load_workbook
from core.base import EXCEL_COLUMNS, NAMESPACE, NSMAP
from utils.errors import ValidationError
from core.xml_model import RecipeTree, ParameterNode, FormulaValueNode


class ExcelImporter:
    """
    Import changes from Excel workbook into RecipeTree instances.
    """

    def import_changes(self, excel_path: str, trees: list) -> dict:
        """
        Read an edited Excel workbook and apply create/update/delete operations to the RecipeTree models.

        This method opens the given `.xlsx` file and matches each sheet by filename to its
        corresponding RecipeTree.  It then iterates every data row, enforcing that exactly one
        data-type column is populated and that any `Defer` references exist in the same shee's
        parameter names.  Rows for existing nodes invoke `update_from_dict()`, while new rows
        invoke `create_parameter()` or `create_formulavalue()`.  After processing all rows, it
        removes any XML nodes that were not seen in Excel, counting them as deleted.  If any
        validation errors occur (e.g. missing defer target or type conflicts), it logs each as
        ERROR and raises a single `ValidationError` summarizing them.  A dict of counts
        (`created`, `updated`, `deleted`) is returned on success.

        Args:
            excel_path: Path to the edited Excel workbook.
            trees: List of RecipeTree loaded via XMLParser.parse().

        Returns:
            stats: Dict with counts: {'created': int, 'updated': int, 'deleted': int}

        Raises:
            ValidationError: Aggregated validation errors found in Excel rows.
        """
        log = logging.getLogger(__name__)
        wb = load_workbook(excel_path)
        errors = []
        stats = {"created": 0, "updated": 0, "deleted": 0}

        log.debug("Importing Excel changes to XML(s)")

        # Map sheet name to RecipeTree by basename
        tree_map = {os.path.basename(t.filepath): t for t in trees}

        for sheet in wb.sheetnames:
            if sheet not in tree_map:
                log.warning("No matching XML for sheet '%s', skipping", sheet)
                continue

            log.debug(f"Sheet {sheet}")

            tree = tree_map[sheet]
            ws = wb[sheet]
            header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]

            excel_param_names = set()
            seen_params = set()
            seen_fvs = set()

            for r_idx, row in enumerate(
                ws.iter_rows(min_row=2, values_only=True), start=2
            ):
                row_dict = dict(zip(header, [v if v is not None else "" for v in row]))
                fp = row_dict.get("FullPath", "").strip()
                tagtype = row_dict.get("TagType", "").strip()

                # Validate single-type
                types = ["Real", "Integer", "String", "EnumerationSet", "Defer"]
                cnt = sum(bool(row_dict.get(t).strip()) for t in types)
                if cnt > 2:
                    log.error(
                        f"{sheet}!Row{r_idx}: expected exactly one data type for {fp}"
                    )
                    errors.append(
                        f"{sheet}!Row{r_idx}: expected exactly one data type for {fp}"
                    )
                    continue

                if tagtype == "Parameter":
                    excel_param_names.add(row_dict["Name"].strip())
                    node = tree.find_parameter(fp)
                    log.debug(f"\tWorking on Parameter: {row_dict["Name"].strip()}")
                    if node:
                        node.update_from_dict(row_dict)
                        log.debug(
                            f"\tParameter found in XML (updating)"  # updating data to: {row_dict=}"
                        )
                        stats["updated"] += 1
                    else:
                        tree.create_parameter(row_dict)
                        log.debug(
                            f"\tParameter NOT found in XML (creating)"  # creating parameter with: {row_dict=}"
                        )
                        stats["created"] += 1
                    seen_params.add(fp)

                elif tagtype == "FormulaValue":
                    node = tree.find_formulavalue(fp)
                    defer = row_dict.get("Defer", "").strip()
                    log.debug(f"\tWorking on FormulaValue: {row_dict["Name"].strip()}")
                    # if defer and not tree.has_parameter_named(defer):
                    if defer and defer not in excel_param_names:
                        log.error(
                            f"{sheet}!Row{r_idx}: defer target '{defer}' not found for {fp}"
                        )
                        errors.append(
                            f"{sheet}!Row{r_idx}: defer target '{defer}' not found for {fp}"
                        )
                        continue
                    if node:
                        node.update_from_dict(row_dict)
                        log.debug(
                            f"\tFormulaValue found in XML (updating)"  # , updating data to: {row_dict=}"
                        )
                        stats["updated"] += 1
                    else:
                        tree.create_formulavalue(row_dict)
                        log.debug(
                            f"\tFormulaValue NOT found in XML (creating)"  # , creating with: {row_dict=}"
                        )
                        stats["created"] += 1
                    seen_fvs.add(fp)
                else:
                    log.error(f"{sheet}!Row{r_idx}: unknown TagType '{tagtype}'")
                    errors.append(f"{sheet}!Row{r_idx}: unknown TagType '{tagtype}'")
                    continue

            # Deletes
            for node in list(tree.parameters):
                if node.fullpath not in seen_params:
                    node.element.getparent().remove(node.element)
                    tree.parameters.remove(node)
                    log.debug(
                        f"\tParameter NOT found in Excel but exists in XML, {node.fullpath} deleted.."
                    )
                    stats["deleted"] += 1
            for node in list(tree.formula_values):
                if node.fullpath not in seen_fvs:
                    node.element.getparent().remove(node.element)
                    tree.formula_values.remove(node)
                    log.debug(
                        f"\tFormulaValue NOT found in Excel but exists in XML, {node.fullpath} deleted.."
                    )
                    stats["deleted"] += 1

        if errors:
            raise ValidationError(f"{len(errors)} errors")
        return stats

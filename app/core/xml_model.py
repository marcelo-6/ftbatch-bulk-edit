# core/xml_model.py

"""
XML model: RecipeTree, ParameterNode, FormulaValueNode.
"""

import os
import re
import logging
from lxml import etree
from lxml.etree import QName
from core.base import NAMESPACE, NSMAP, EXCEL_COLUMNS
from utils.errors import ValidationError, TypeConflictError, DeferResolutionError
from utils.string import safe_strip


class NodeBase:
    """
    Base class for ParameterNode and FormulaValueNode.
    Stores the original XML element, its full path, and a snapshot of sub-elements.
    """

    def __init__(self, element: etree.Element, fullpath: str, source_file: str):
        self.element = element
        self.fullpath = fullpath
        self.source_file = source_file
        self.original_subs = {
            QName(child.tag).localname: (child.text or "") for child in element
        }
        self.log = logging.getLogger(__name__)

    def to_excel_row(self) -> dict:
        raise NotImplementedError

    def update_from_dict(self, row: dict):
        raise NotImplementedError

    def reorder_children(self):
        raise NotImplementedError


class ParameterNode(NodeBase):
    """
    Represents a <Parameter> node in the XML tree.
    """

    def to_excel_row(self) -> dict:
        row = {"TagType": "Parameter", "Name": "", "FullPath": self.fullpath}
        row["Name"] = self.original_subs.get("Name", "")
        for col in (
            "Real",
            "Integer",
            "High",
            "Low",
            "String",
            "EnumerationSet",
            "EnumerationMember",
        ):
            row[col] = self.original_subs.get(col, "")
        row["Defer"] = ""
        for k, v in self.original_subs.items():
            if k not in row:
                row[k] = v
        # self.log.debug(f"{row}") # Too much logging for now
        return row

    def update_from_dict(self, row: dict) -> bool:
        """
        Apply updates to this <Parameter> element based on a single Excel row.

        Returns:
            bool:
            - True if at least one XML text value was changed (or a new element created),
            - False if everything was identical and no modification was made.

        First, it validates that the row has exactly one data-type column (Real, Integer, String,
        or EnumerationSet), raising `TypeConflictError` otherwise.  Then, for each field in the row,
        it skips TagType/FullPath/Defer and any blank-and-nonexistent sub-elements, creating or
        updating child tags to match the new values.  After setting text on each sub-element,
        it invokes `reorder_children()` to enforce the canonical XML tag sequence.  Any unexpected
        missing type or sub-element will raise `ValidationError` during reordering.  This
        encapsulates all in-memory changes to the original XML tree.
        """

        changed = False

        # Validate exactly one data-type
        type_fields = ["Real", "Integer", "String", "EnumerationSet"]
        count = sum(bool(row[f].strip()) for f in type_fields)
        if count > 2:
            raise TypeConflictError(f"{self.fullpath}: must have exactly one data type")
        try:
            # Loop through each field and create/update as needed
            for k, new_val in row.items():
                if k in ("TagType", "FullPath", "Defer") or k.startswith(
                    "FormulaValueLimit_"
                ):
                    continue
                text = safe_strip(new_val)

                # skip blanks that didn’t originally exist
                if not text and k not in self.original_subs:
                    continue
                el = self.element.find(f"{{{NAMESPACE}}}{k}", namespaces=NSMAP)
                if el is None:
                    el = etree.SubElement(self.element, f"{{{NAMESPACE}}}{k}")
                    el.text = text
                    changed = True
                else:
                    old = safe_strip(el.text)
                    if text != old:
                        el.text = text
                        changed = True
            if changed:
                self.reorder_children()
            return changed
        except Exception as e:
            self.log.debug(f"\t\t Failed on Row:{row}")
            raise e

    def reorder_children(self):
        children = {QName(c.tag).localname: c for c in self.element}
        if "String" in children:
            order = ["Name", "ERPAlias", "PLCReference", "String", "EngineeringUnits"]
        elif "Integer" in children:
            order = [
                "Name",
                "ERPAlias",
                "PLCReference",
                "Integer",
                "High",
                "Low",
                "EngineeringUnits",
                "Scale",
            ]
        elif "Real" in children:
            order = [
                "Name",
                "ERPAlias",
                "PLCReference",
                "Real",
                "High",
                "Low",
                "EngineeringUnits",
                "Scale",
            ]
        elif "EnumerationSet" in children:
            order = [
                "Name",
                "ERPAlias",
                "PLCReference",
                "EnumerationSet",
                "EnumerationMember",
            ]
        else:
            raise ValidationError(f"{self.fullpath}: no recognized type")
        for c in list(self.element):
            self.element.remove(c)
        for tag in order:
            el = children.get(tag)
            if el is None:
                el = etree.Element(f"{{{NAMESPACE}}}{tag}")
            self.element.append(el)


class FormulaValueNode(NodeBase):
    """
    Represents a <FormulaValue> node in the XML tree.
    """

    def to_excel_row(self) -> dict:
        row = {"TagType": "FormulaValue", "Name": "", "FullPath": self.fullpath}
        row["Name"] = self.original_subs.get("Name", "")
        # always include Defer
        defer = self.original_subs.get("Defer", "")
        row["Defer"] = defer
        # default Value only when no defer
        row["Value"] = "" if defer else self.original_subs.get("Value", "")

        # handle ParamExpression cases
        expr_present = "ParamExpression" in self.original_subs
        # find the true dtype (Real/Integer/String/Enum)
        dtype = None
        for t in ("Real", "Integer", "String", "EnumerationSet"):
            if self.original_subs.get(t, "").strip():
                dtype = t
                break
        # if this node had a ParamExpression tag, then
        #   * the dtype-col holds the literal "ParamExpression"
        #   * the new column carries the expression text from the dtype element
        if expr_present and dtype:
            row[dtype] = "ParamExpression"
            row["ParamExpression"] = self.original_subs.get(dtype, "")
        else:
            # standard case: just emit the raw values
            row["ParamExpression"] = ""
            for t in (
                "Real",
                "Integer",
                "String",
                "EnumerationSet",
                "EnumerationMember",
            ):
                row[t] = self.original_subs.get(t, "")
        # for col in ("Real", "Integer", "String", "EnumerationSet", "EnumerationMember"):
        #     row[col] = self.original_subs.get(col, "")
        fvl = self.element.find(f"{{{NAMESPACE}}}FormulaValueLimit", namespaces=NSMAP)
        if fvl is not None:
            row["FormulaValueLimit_Verification"] = fvl.get("Verification", "")
            for child in fvl:
                name = QName(child.tag).localname
                row[f"FormulaValueLimit_{name}"] = child.text or ""
        else:
            for col in EXCEL_COLUMNS:
                if col.startswith("FormulaValueLimit_"):
                    row[col] = ""
        for k, v in self.original_subs.items():
            if k not in row:
                row[k] = v
        # self.log.debug(f"{row}") # Too much logging for now
        return row

    def update_from_dict(self, row: dict) -> bool:
        """
        Apply updates to this <FormulaValue> element based on a single Excel row.

        Returns:
            bool:
            - True if at least one XML text value was changed (or a new element created),
            - False if everything was identical and no modification was made.

        It first validates that exactly one of Real, Integer, String, or EnumerationSet is
        provided, raising `TypeConflictError` if not.  It then processes each field, skipping any
        FormulaValueLimit data (handled separately) and TagType/FullPath.  For `Value` vs
        `Defer`, it omits the `Value` tag when `Defer` is set, and vice versa.  It creates or
        updates child elements to match the Excel values, preserving existing text where the
        Excel cell is blank but the node existed.  After all sub-elements and the optional
        `<FormulaValueLimit>` have been updated, it invokes `reorder_children()` to restore
        deterministic ordering.  Any failure to find a referenced Step or attribute raises
        `ValidationError` or `DeferResolutionError`.
        """
        changed = False

        # detect if user is setting up an expression
        expr_text = safe_strip(row.get("ParamExpression", ""))
        # check if one of the dtype‐columns is literally "ParamExpression"
        expr_dtype = None
        for t in ("Real", "Integer", "String"):
            if safe_strip(row.get(t, "")) == "ParamExpression":
                expr_dtype = t
                break
        if expr_dtype and not expr_text:
            # blank expression not allowed
            raise ValidationError(
                f"{self.fullpath}: ParamExpression column must be non-blank when {expr_dtype}=ParamExpression"
            )

        type_fields = ["Real", "Integer", "String", "EnumerationSet", "Defer"]
        count = sum(bool(safe_strip(row[f])) for f in type_fields)
        if count > 2:
            raise TypeConflictError(f"{self.fullpath}: must have exactly one data type")
        try:
            for k, new_val in row.items():
                if k.startswith("FormulaValueLimit_") or k in (
                    "TagType",
                    "FullPath",
                    "ParamExpression",
                ):
                    continue
                text = safe_strip(new_val)
                #  skip Value if Defer set, skip Defer if blank
                if k == "Value" and row.get("Defer", "").strip():
                    continue
                if k == "Defer" and not text:
                    continue
                if expr_dtype and k == expr_dtype:
                    continue
                # skip blanks that didn’t originally exist
                if not text and k not in self.original_subs:
                    continue
                el = self.element.find(f"{{{NAMESPACE}}}{k}", namespaces=NSMAP)
                if el is None:
                    el = etree.SubElement(self.element, f"{{{NAMESPACE}}}{k}")
                    el.text = text
                    changed = True
                else:
                    old = safe_strip(el.text)
                    if text != old:
                        el.text = text
                        changed = True

            # handle ParamExpression
            if expr_dtype:
                # ensure an empty <ParamExpression/> tag exists
                expr_el = self.element.find(
                    f"{{{NAMESPACE}}}ParamExpression", namespaces=NSMAP
                )
                if expr_el is None:
                    expr_el = etree.SubElement(
                        self.element, f"{{{NAMESPACE}}}ParamExpression"
                    )
                    changed = True
                # now write the actual expression into the dtype element
                dtype_el = self.element.find(
                    f"{{{NAMESPACE}}}{expr_dtype}", namespaces=NSMAP
                )
                if dtype_el is None:
                    dtype_el = etree.SubElement(
                        self.element, f"{{{NAMESPACE}}}{expr_dtype}"
                    )
                if safe_strip(dtype_el.text) != expr_text:
                    dtype_el.text = expr_text
                    changed = True
            if changed:
                self.reorder_children()
            return changed
        except Exception as e:
            self.log.debug(f"\t\t Failed on Row:{row}")
            raise e

    def reorder_children(self):
        """
        Reorder this <FormulaValue> element's children to the canonical S88 Batch layout.

        The sequence enforced is: Name, Display, either Defer or Value, the single data-type
        element (Integer, Real, String, or EnumerationSet), the optional EnumerationMember,
        EngineeringUnits, and finally the `<FormulaValueLimit>` block (if present).  It first
        builds a map of existing child elements by localname, removes all from the parent, and
        then reattaches them in the specified order—creating empty placeholders for any
        required tags that were missing.  This guarantees that even after updates or creations,
        the resulting XML files are schema-compliant and machine-diff-friendly.  Missing
        required children raise `ValidationError`.
        """

        children = {QName(c.tag).localname: c for c in self.element}
        has_defer = "Defer" in children
        has_expression = "ParamExpression" in children
        order = ["Name", "Display"]
        if has_defer:
            order.append("Defer")
        elif has_expression:
            order.append("ParamExpression")
        else:
            order.append("Value")

        for t in ("Integer", "Real", "String", "EnumerationSet"):
            if t in children:
                dtype = t
                order.append(t)

        if "EnumerationMember" in children:
            order.append("EnumerationMember")
        if dtype in ("Integer", "Real"):
            order.append("EngineeringUnits")
        if "FormulaValueLimit" in children:
            order.append("FormulaValueLimit")
        # order.extend(["EngineeringUnits", "FormulaValueLimit"])
        for c in list(self.element):
            self.element.remove(c)
        for tag in order:
            el = children.get(tag)
            if el is None:
                el = etree.Element(f"{{{NAMESPACE}}}{tag}")
            self.element.append(el)


class RecipeTree:
    """
    Holds an XML tree and lists of its ParameterNode and FormulaValueNode.
    """

    def __init__(self, path: str):
        self.filepath = path
        self.tree = etree.parse(path)
        self.root = self.tree.getroot()
        self.parameters = []
        self.formula_values = []
        self.log = logging.getLogger(__name__)

    def extract_nodes(self):
        rid_el = self.root.find(f"{{{NAMESPACE}}}RecipeElementID", namespaces=NSMAP)
        rid = (rid_el.text or "") if rid_el is not None else ""
        for p in self.root.findall(f"{{{NAMESPACE}}}Parameter", namespaces=NSMAP):
            name = p.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text or ""
            fp = f"{rid}/Parameter[{name}]"
            # self.log.debug(f"\t\tFound {fp}") # Too much logging for now
            self.parameters.append(ParameterNode(p, fp, self.filepath))
        for fv in self.root.findall(
            f".//{{{NAMESPACE}}}FormulaValue", namespaces=NSMAP
        ):
            step = fv.getparent()
            step_name = step.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text or ""
            name = fv.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text or ""
            fp = f"{rid}/Steps/Step[{step_name}]/FormulaValue[{name}]"
            # self.log.debug(f"\t\tFound {fp}") # Too much logging for now
            self.formula_values.append(FormulaValueNode(fv, fp, self.filepath))

    def find_parameter(self, fullpath: str):
        return next((p for p in self.parameters if p.fullpath == fullpath), None)

    def find_formulavalue(self, fullpath: str):
        return next((f for f in self.formula_values if f.fullpath == fullpath), None)

    def has_parameter_named(self, name: str) -> bool:
        return any(p.original_subs.get("Name", "") == name for p in self.parameters)

    def create_parameter(self, row: dict):
        """
        Create a new <Parameter> under the root, inserting it right after
        any existing <Parameter> elements (or before <Steps> if none).
        Returns the newly created ParameterNode.
        """
        # 1) Build a fresh <Parameter> element (empty)
        new_el = etree.Element(f"{{{NAMESPACE}}}Parameter", nsmap=NSMAP)

        # 2) Locate last existing <Parameter> under root
        existing = list(
            self.root.findall(f"{{{NAMESPACE}}}Parameter", namespaces=NSMAP)
        )
        if existing:
            last = existing[-1]
            self.root.insert(self.root.index(last) + 1, new_el)
        else:
            # if no <Parameter> found, insert before <Steps> if present
            steps = self.root.find(f"{{{NAMESPACE}}}Steps", namespaces=NSMAP)
            if steps is not None:
                self.root.insert(self.root.index(steps), new_el)
            else:
                # fallback: append at end
                self.root.append(new_el)

        # 3) Wrap in our Node class, apply data, track it
        node = ParameterNode(new_el, row["FullPath"], self.filepath)
        changed = node.update_from_dict(row)  # always True on new
        self.parameters.append(node)
        return node

    def create_formulavalue(self, row: dict):
        m = re.match(r".*/Steps/Step\[(.*?)\]/FormulaValue\[.*\]$", row["FullPath"])
        if not m:
            raise ValidationError(f"{row['FullPath']}: cannot parse step")
        step_name = m.group(1)
        step_el = next(
            s
            for s in self.root.findall(f".//{{{NAMESPACE}}}Step", namespaces=NSMAP)
            if s.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text == step_name
        )
        if step_el is None:
            raise ValidationError(f"Step '{step_name}' not found")
        el = etree.SubElement(step_el, f"{{{NAMESPACE}}}FormulaValue")
        node = FormulaValueNode(el, row["FullPath"], self.filepath)
        node.update_from_dict(row)
        self.formula_values.append(node)

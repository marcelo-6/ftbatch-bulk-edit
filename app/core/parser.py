"""
XMLParser: recursively load parent and child XMLs into RecipeTree instances.
"""

import os
import logging
from core.xml_model import RecipeTree
from core.base import NSMAP


class XMLParser:
    """
    Parses a .pxml/.uxml tree with recursive child loading.
    """

    def parse(self, parent_path: str) -> list:
        """
        Recursively load a parent XML recipe and all of its child recipe files into RecipeTree objects.

        This method begins by loading the parent `.pxml` (or `.uxml`) file, creating a RecipeTree
        instance that captures its parameters and formula values.  It then inspects every
        `<StepRecipeID>` element to discover child files (e.g. `.uxml` or `.oxml`) in the same directory,
        loading each of those exactly once.  For each load, it logs an INFO line indicating how many
        parameters and formula values were extracted.  If a referenced child file is missing, it emits
        a warning but continues processing.  Finally, it returns a list of all distinct RecipeTree
        objects (parent plus children), preserving the original loading order.
        """
        loaded = {}
        log = logging.getLogger(__name__)

        def _load(path):
            log.info("Parsing XML: %s", path)
            if path in loaded:
                return
            tree = RecipeTree(path)
            tree.extract_nodes()
            loaded[path] = tree

            log.info(
                f"\tLoaded {os.path.basename(path)}: {len(tree.parameters)} params, {len(tree.formula_values)} formula values, Total = {len(tree.parameters) + len(tree.formula_values)}"
            )
            # determine child extension
            ext = os.path.splitext(path)[1].upper()
            child_ext = {".PXML": ".UXML", ".UXML": ".OXML"}.get(ext)
            if child_ext:
                for sr in tree.tree.findall(
                    f".//{{{NSMAP[None]}}}StepRecipeID", namespaces=NSMAP
                ):
                    name = (sr.text or "").strip()
                    if not name:
                        continue
                    child = os.path.join(os.path.dirname(path), name + child_ext)
                    log.debug(
                        f"\tParent {os.path.basename(path)} - Looking for Child XML: {child}",
                    )
                    if os.path.exists(child):
                        log.debug(
                            f"\tParent {os.path.basename(path)} - Child found, Parsing Child XML: {child}"
                        )
                        _load(child)
                    else:
                        log.warning(
                            f"\tParent {os.path.basename(path)} - Child XML not found: {child}"
                        )

        _load(parent_path)
        return list(loaded.values())

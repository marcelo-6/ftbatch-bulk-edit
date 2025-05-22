# core/xml_model.py

"""
XML model: RecipeTree, ParameterNode, FormulaValueNode.
"""

import os
import re
from lxml import etree
from lxml.etree import QName
from core.base import NAMESPACE, NSMAP, EXCEL_COLUMNS
from utils.errors import ValidationError, TypeConflictError, DeferResolutionError


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
        return row

    def update_from_dict(self, row: dict):
        type_fields = ["Real", "Integer", "String", "EnumerationSet"]
        count = sum(bool(row[f].strip()) for f in type_fields)
        if count > 2:
            raise TypeConflictError(f"{self.fullpath}: must have exactly one data type")
        for k, new_val in row.items():
            if k in ("TagType", "FullPath", "Defer") or k.startswith(
                "FormulaValueLimit_"
            ):
                continue
            text = new_val.strip()
            if not text and k not in self.original_subs:
                continue
            el = self.element.find(f"{{{NAMESPACE}}}{k}", namespaces=NSMAP)
            if el is None:
                el = etree.SubElement(self.element, f"{{{NAMESPACE}}}{k}")
            el.text = text
        self.reorder_children()

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
        defer = self.original_subs.get("Defer", "")
        row["Defer"] = defer
        row["Value"] = "" if defer else self.original_subs.get("Value", "")
        for col in ("Real", "Integer", "String", "EnumerationSet", "EnumerationMember"):
            row[col] = self.original_subs.get(col, "")
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
        return row

    def update_from_dict(self, row: dict):
        type_fields = ["Real", "Integer", "String", "EnumerationSet", "Defer"]
        count = sum(bool(row[f].strip()) for f in type_fields)
        if count > 2:
            raise TypeConflictError(f"{self.fullpath}: must have exactly one data type")
        for k, new_val in row.items():
            if k.startswith("FormulaValueLimit_") or k in ("TagType", "FullPath"):
                continue
            text = new_val.strip()
            if k == "Value" and row.get("Defer", "").strip():
                continue
            if k == "Defer" and not text:
                continue
            if not text and k not in self.original_subs:
                continue
            el = self.element.find(f"{{{NAMESPACE}}}{k}", namespaces=NSMAP)
            if el is None:
                el = etree.SubElement(self.element, f"{{{NAMESPACE}}}{k}")
            el.text = text
        # Assume FVL update logic as before...
        self.reorder_children()

    def reorder_children(self):
        children = {QName(c.tag).localname: c for c in self.element}
        has_defer = "Defer" in children
        order = ["Name", "Display"] + (["Defer"] if has_defer else ["Value"])
        for t in ("Integer", "Real", "String", "EnumerationSet"):
            if t in children:
                order.append(t)
        if "EnumerationMember" in children:
            order.append("EnumerationMember")
        order.extend(["EngineeringUnits", "FormulaValueLimit"])
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

    def extract_nodes(self):
        rid_el = self.root.find(f"{{{NAMESPACE}}}RecipeElementID", namespaces=NSMAP)
        rid = (rid_el.text or "") if rid_el is not None else ""
        for p in self.root.findall(f"{{{NAMESPACE}}}Parameter", namespaces=NSMAP):
            name = p.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text or ""
            fp = f"{rid}/Parameter[{name}]"
            self.parameters.append(ParameterNode(p, fp, self.filepath))
        for fv in self.root.findall(
            f".//{{{NAMESPACE}}}FormulaValue", namespaces=NSMAP
        ):
            step = fv.getparent()
            step_name = step.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text or ""
            name = fv.find(f"{{{NAMESPACE}}}Name", namespaces=NSMAP).text or ""
            fp = f"{rid}/Steps/Step[{step_name}]/FormulaValue[{name}]"
            self.formula_values.append(FormulaValueNode(fv, fp, self.filepath))

    def find_parameter(self, fullpath: str):
        return next((p for p in self.parameters if p.fullpath == fullpath), None)

    def find_formulavalue(self, fullpath: str):
        return next((f for f in self.formula_values if f.fullpath == fullpath), None)

    def has_parameter_named(self, name: str) -> bool:
        return any(p.original_subs.get("Name", "") == name for p in self.parameters)

    def create_parameter(self, row: dict):
        el = etree.SubElement(self.root, f"{{{NAMESPACE}}}Parameter")
        node = ParameterNode(el, row["FullPath"], self.filepath)
        node.update_from_dict(row)
        self.parameters.append(node)

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

# Bulk Editor for FactoryTalk Batch Recipes

A command-line tool (Python-based) that lets engineers bulk-edit Rockwell FactoryTalk Batch S88 recipes (`.pxml`, `.uxml`, and `.oxml`) by round-tripping through Excel. You can **export** your recipes (including any child references) into a spreadsheet, make batch changes to parameters and formula-values, then **import** the edits back to produce updated XML files—preserving element order, empty tags, and original structure.

---

## Table of Contents

- [Bulk Editor for FactoryTalk Batch Recipes](#bulk-editor-for-factorytalk-batch-recipes)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Using pip](#using-pip)
    - [Using a Python Virtual Environment](#using-a-python-virtual-environment)
    - [Using uv as the Package Manager](#using-uv-as-the-package-manager)
    - [Using the Makefile (Recommended)](#using-the-makefile-recommended)
  - [Usage Overview](#usage-overview)
    - [Export XML to Excel (`xml2excel`)](#export-xml-to-excel-xml2excel)
    - [Import Excel to XML (`excel2xml`)](#import-excel-to-xml-excel2xml)
  - [Debug Mode](#debug-mode)
  - [Flow Chart](#flow-chart)
  - [Example Excel Output](#example-excel-output)
  - [Example XML Schema Snippet](#example-xml-schema-snippet)
  - [Preservation Rules \& Edge Cases](#preservation-rules--edge-cases)
  - [Troubleshooting](#troubleshooting)

---

## Features

1. **Bulk Editing in Excel**  
   - Extract top-level `<Parameter>` and step-level `<FormulaValue>` into one sheet per file.  
   - Edit hundreds of tags in your favorite spreadsheet tool.  

2. **Preserve Order & Empties**  
   - Maintains the original element order.  
   - Keeps empty tags (e.g. `<EngineeringUnits/>`, `<String/>`).  
   - Retains existing `<FormulaValueLimit>` blocks unless you remove them.  

3. **Recursive Child Parsing**  
   - A `.pxml` may reference `.uxml`; a `.uxml` may reference `.oxml` via `<StepRecipeID>`.  
   - Exports all related files into one workbook.

4. **Selective Create/Update/Delete**  
   - **Update** if a row’s `FullPath` matches an existing node.  
   - **Delete** if you remove a row entirely.  
   - **Create** if you add a new `FullPath` row (with one valid data-type column).

5. **Detailed Logging**  
   - INFO-level messages to console.  
   - DEBUG-level (with `--debug`) to `batch_bulk_editor.log`.

---

## Requirements

- **Python 3.7+** (tested on 3.12)  
- **lxml**  
- **openpyxl**  

---

## Installation

### Using pip

1. **Clone** this repo.  
2. **Install** dependencies:

   ```bash
   pip install lxml openpyxl
   ```

3. **Run**:

   ```bash
   python main.py xml2excel --xml yourRecipe.pxml --excel out.xlsx
   ```

### Using a Python Virtual Environment

1. ```bash
   python -m venv venv
   ```
2. Activate it:

   * Windows: `venv\Scripts\activate`
   * macOS/Linux: `source venv/bin/activate`
3. Install:

   ```bash
   pip install lxml openpyxl
   ```
4. Run:

   ```bash
   python main.py xml2excel --xml yourRecipe.pxml --excel out.xlsx
   ```

### Using uv as the Package Manager

If you’ve defined your dependencies in `pyproject.toml`:

```bash
uv init
uv install
uv run python main.py xml2excel --xml yourRecipe.pxml --excel out.xlsx
```

### Using the Makefile (Recommended)

We provide a Makefile to automate all steps:

```bash
make help       # list targets
make test       # runs pytests
make all        # check-uv → install → meta → version → build → clean
make install    # uv init + uv sync
make meta       # print name/version/description
make version    # generate Windows version_info.txt
make build      # bundle source for Windows
make clean      # remove build artifacts
```

---

## Usage Overview

### Export XML to Excel (`xml2excel`)

```bash
python main.py xml2excel --xml PATH_TO_XML --excel OUTPUT_XLSX [--debug]
```

| Argument  | Description                                                                       |
| --------- | --------------------------------------------------------------------------------- |
| `--xml`   | Parent file (`.pxml`, `.uxml`, or `.oxml`). Children loaded via `<StepRecipeID>`. |
| `--excel` | Destination Excel workbook.                                                       |
| `--debug` | Write DEBUG logs to `batch_bulk_editor.log`.                                      |

### Import Excel to XML (`excel2xml`)

```bash
python main.py excel2xml --xml PATH_TO_XML --excel EDITED_XLSX [--debug]
```

| Argument  | Description                                  |
| --------- | -------------------------------------------- |
| `--xml`   | Same parent file used for export.            |
| `--excel` | Edited Excel workbook.                       |
| `--debug` | Write DEBUG logs to `batch_bulk_editor.log`. |

---

## Debug Mode

Add `--debug` before the subcommand to capture detailed logs:

```bash
python main.py --debug xml2excel --xml myRecipe.pxml --excel out.xlsx
```

* Creates/appends `batch_bulk_editor.log` at DEBUG level.
* Console remains at INFO level.

---

## Flow Chart

```mermaid
flowchart LR
  subgraph XML2Excel
    A1([Start]) --> A2{XML exists?}
    A2 -- No --> A3([Error & Exit])
    A2 -- Yes --> A4[Parse parent & children]
    A4 --> A5[Extract nodes → row dicts]
    A5 --> A6[Write Excel workbook]
    A6 --> A7([Done])
  end

  subgraph Excel2XML
    B1([Start]) --> B2{XML exists?}
    B2 -- No --> B3([Error & Exit])
    B2 -- Yes --> B4[Load original XML → RecipeTree]
    B4 --> B5[Read Excel rows]
    B5 --> B6{"Row = existing/new/missing?"}
    B6 -- existing --> B7[update node]
    B6 -- new      --> B8[create node]
    B6 -- missing  --> B9[delete node]
    B7 --> B10[Reorder & write XML]
    B8 --> B10
    B9 --> B10
    B10 --> B11([Done])
  end

  XML2Excel -.-> Excel2XML
```

---

## Example Excel Output

| FullPath                                                             | TagType      | Name                     | Real | Integer | String | EnumerationSet   | EnumerationMember | Defer            | FormulaValueLimit\_Verification | … |
| -------------------------------------------------------------------- | ------------ | ------------------------ | ---- | ------- | ------ | ---------------- | ----------------- | ---------------- | ------------------------------- | - |
| TEST/Parameter\[XFER5\_TARGET\_CONC\_DB]                             | Parameter    | XFER5\_TARGET\_CONC\_DB  | 0    |         |        |                  |                   |                  |                                 |   |
| TEST/Steps/Step\[ACQ\_REL:1]/FormulaValue\[X\_R\_END\_PHASE\_PROMPT] | FormulaValue | X\_R\_END\_PHASE\_PROMPT |      |         |        | N\_DISABLEENABLE | DISABLE           |                  | No\_Limits                      |   |
| TEST/Steps/Step\[ACQ\_REL:1]/FormulaValue\[X\_R\_END\_TYPE]          | FormulaValue | X\_R\_END\_TYPE          |      |         |        | N\_ENDTYPE       |                   | AQREL\_END\_TYPE | No\_Limits                      |   |

---

## Example XML Schema Snippet

```xml
<xs:element name="Parameter">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Name" type="xs:string" minOccurs="0"/>
      <xs:element name="ERPAlias" minOccurs="0"/>
      <xs:element name="PLCReference" type="xs:unsignedByte" minOccurs="0"/>
      <xs:element name="Real" type="xs:unsignedShort" minOccurs="0"/>
      <xs:element name="High" type="xs:unsignedShort" minOccurs="0"/>
      <xs:element name="Low" type="xs:unsignedByte" minOccurs="0"/>
      <xs:element name="EngineeringUnits" type="xs:string" minOccurs="0"/>
      <xs:element name="Scale" type="xs:boolean" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>

<xs:element name="FormulaValue">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="Name" type="xs:string" minOccurs="0"/>
      <xs:element name="Display" type="xs:boolean" minOccurs="0"/>
      <xs:element name="Value" minOccurs="0"/>
      <xs:element name="Defer" type="xs:string" minOccurs="0"/>
      <xs:element name="Real" type="xs:decimal" minOccurs="0"/>
      <xs:element name="EngineeringUnits" type="xs:string" minOccurs="0"/>
      <xs:element name="FormulaValueLimit" minOccurs="0">
        <xs:complexType>
          <xs:attribute name="Verification" type="xs:string" use="optional"/>
          <xs:sequence>
            <xs:element name="LowValue" type="xs:decimal" minOccurs="0"/>
            <xs:element name="HighValue" type="xs:decimal" minOccurs="0"/>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

---

## Preservation Rules & Edge Cases

* **Empty Tags**: If a sub-element existed (even empty), it remains.
* **Create FormulaValueLimit** only if `FormulaValueLimit_*` columns are non-blank or it existed originally.
* **Type Enforcement**: Exactly one of Real, Integer, String, or EnumerationSet per row.
* **Defer Validation**: A `<FormulaValue>`’s `Defer` must match a parameter name in the same sheet.

---

## Troubleshooting

1. **No Sheet Found**

   * Sheet name must match the XML filename (`TEST.pxml` → sheet “TEST.pxml”).
2. **Missing Data-Type**

   * Every Parameter or FormulaValue row must have one and only one data-type column.
3. **Need More Logs?**

   * Add `--debug` to capture detailed steps in `batch_bulk_editor.log`.

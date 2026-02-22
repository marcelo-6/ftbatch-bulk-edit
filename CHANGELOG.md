<!-- markdownlint-disable -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6] - 2026-02-22

### <!-- 1 -->Bug Fixes
- Run tag-version step with bash on windows runner  by @marcelo-6 ([070bc70](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/070bc70d63e2b4c24b3b6c7d57da513dec812c47))

- Rename Windows exe to include tag version before upload  by @marcelo-6 ([9f96911](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/9f969113bc5b1a6032b31183d559e0b5f784a6e4))


## [0.2.5] - 2026-02-22

### <!-- 1 -->Bug Fixes
- Run create_release even if publish_pypi fails by using always() while requiring windows build success  by @marcelo-6 ([174a039](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/174a039267459605198311cfe526f7c5bde58779))


## [0.2.4] - 2026-02-22

### <!-- 7 -->Miscellaneous Tasks
- Make create_release depend on build_windows success but ignore publish_pypi failure  by @marcelo-6 ([4284d87](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/4284d875ccca38e350c5ae56927f41b71b2359f8))


## [0.2.3] - 2026-02-22

### <!-- 3 -->Documentation
- Added more classifiers to pyproject.toml metadata  by @marcelo-6 ([732eb77](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/732eb77221506e509134ef3fce01492d09de0bac))


## [0.2.2] - 2026-02-22

### <!-- 5 -->Styling
- Updated after lint  by @marcelo-6 ([36a6587](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/36a65870590fc856a13474ef15b4f447da90a45e))


## [0.2.1] - 2026-02-22

### <!-- 1 -->Bug Fixes
- Use windows-shell (Git Bash) to avoid WSL bash on GitHub runners  by @marcelo-6 ([dbbcac0](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/dbbcac049285e4239407b050f9e8e84736004f71))


### <!-- 3 -->Documentation
- Changed development status to stable  by @marcelo-6 ([7a234e3](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/7a234e334c8486245dc0fb9c41f581560faa9f15))

- Preparing for pypi release  by @marcelo-6 ([9c21a5a](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/9c21a5abe0189d6f6b7d0b38d8032948aba80755))

- Added license  by @marcelo-6 ([07df3a4](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/07df3a4d269c1903c0359907a22f858a0421edac))

- Cleaner documentation  by @marcelo-6 ([e21353c](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/e21353c91d19e865dc3f1e16e44b417144e4a07a))


### <!-- 7 -->Miscellaneous Tasks
- Simplified publish it seems test.pypi gives 503 even on success  by @marcelo-6 ([cbf1fa9](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/cbf1fa9b4f0ea2a367a4b324fcc95f149c5f0ce1))

- Added retry to publish step  by @marcelo-6 ([2aa41c9](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/2aa41c9b674969f040880949d4db8bbdb82e0ee4))

- Updated to accept windows shell for windows build  by @marcelo-6 ([1b26923](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/1b26923196d91e3231f6adbf97be1551ef11bd94))

- Updated action versions to latest  by @marcelo-6 ([e180f01](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/e180f01c8e3ef19ff16868d91bee372d83c835fd))

- Added dynamic release version to pypi publish step  by @marcelo-6 ([08c631b](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/08c631baa3adb628c605ec5f0776a6628fade121))

- Route GitHub workflows through just and centralize packaging/publish commands  by @marcelo-6 ([a15d66c](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/a15d66c1ba497be6df1a704369a7a217ae9cf78a))


### Other
- Fixing failed build  by @marcelo-6 ([5833d15](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/5833d15ce70f964575e65ed9e3b3fff4feac21c7))

- Added better tooling to locally test publish pipeline  by @marcelo-6 ([65a6b92](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/65a6b92e61eced8bacd497f26d84be6cc47fa949))


## [0.2.0] - 2026-02-21

### <!-- 0 -->Features
- Added rich output for Typer and tests  by @marcelo-6 ([b1600cd](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/b1600cde2b6619c0023f51e6ee6846c81e40eda3))

- Migrated from argparse to Typer  by @marcelo-6 ([559e50a](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/559e50af64e3e1898e84c95dc4dbeeaccdc86376))

- Task runner replaced with Justfile  by @marcelo-6 ([3049ab4](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/3049ab4006a97f9ace4155b64ca9e5319939dc84))

- Added deferrals count to output  by @marcelo-6 ([2489de5](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/2489de5bb4ef8ea0e204e80c98638e8df1a1dac5))

- Added better summary for what changes were made for excel2xml  by @marcelo-6 ([3c5fb32](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/3c5fb32410ec0d8659006e958169ccf0e1317577))

- Support ParamExpression in FormulaValue  by @marcelo-6 ([f078860](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/f0788603c7908525c932e8ae28ef3c3e7a4f2971))

- Auto-size columns to fit content  by @marcelo-6 ([600f627](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/600f6278eeb26ea4cdc6fcf8e6dbe40bcc2bc6c0))

- Insert new <Parameter> nodes in correct position  by @marcelo-6 ([6f7c60d](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/6f7c60dc7bb0e222ef2dd8b6a097b80abbe71fa1))

- Added proper tracker of updated parameters  by @marcelo-6 ([b0a5ac6](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/b0a5ac6a483f385d9f4d8642cf6f59a5623da47c))

- Add Make commands, making it easier to build / prepare to build. The pyinstaller still needs to run from windows  by @marcelo-6 ([0a3f0bc](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/0a3f0bc3657b045b1d4b77f4e0e658c53b9a7121))

- Add Make commands, making it easier to build / prepare to...  by @marcelo-6 ([d2464d1](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/d2464d131a20ad9ca2d2618453bc8f1a97c369fd))


### <!-- 1 -->Bug Fixes
- Fixed return of import changes from ExcelImporter  by @marcelo-6 ([4cc4d78](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/4cc4d7867f80f63690eea8a71e96de7b105934e9))

- Fixed the way ParamExpression types are represented in excel  by @marcelo-6 ([1953392](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/19533923e864d5ff111500f453a5d0fa9a47d91d))

- Added save string strip for whern the excel sheet has boolean values (FALSE) for the scale cells for example  by @marcelo-6 ([6216719](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/62167196fed4538df434017c7e17099a1ee98087))

- Add extended debug logging  by @marcelo-6 ([10b171b](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/10b171b07e4e985cc84e709bc4a9340f29ff9633))

- Order of new parameters creation is now pre-determined  by @marcelo-6 ([c6b4697](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/c6b469744c0e38525c24222ec5a8146932aa9992))

- Fix gitignore  by @marcelo-6 ([ba7ef69](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/ba7ef69fdc5a7d37427b891fe5c89a558d4b7649))

- Fix  by @marcelo-6 ([78ddf04](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/78ddf0481413c9db06563f03a2403989fda2f72f))

- Fixed123  by @marcelo-6 ([d5d048a](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/d5d048a05d810a14a4283178dddfaf103d53bc7e))

- Fixedd  by @marcelo-6 ([9b496db](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/9b496dbbb3a35b829f06323f904e7be78df359fa))

- Fixed  by @marcelo-6 ([2a9012b](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/2a9012bbf21ecff748def83d4ea1d9be9fc43508))


### <!-- 2 -->Refactor
- Reorganized code to make it easier to troubleshoot and read  by @marcelo-6 ([8519ef5](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/8519ef54d6e6fb2c6344bc2dbaaa8ac8e464266f))


### <!-- 3 -->Documentation
- Added most update info to documentation  by @marcelo-6 ([2b756b1](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/2b756b1a089d260d424ac529d6a4a654fccf680d))

- Add better decstring to some functions/methods and added more example xmls  by @marcelo-6 ([9b8a058](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/9b8a05821e7ac6194e329097060a175fde06fd77))


### <!-- 6 -->Testing
- Fixed test for new parser counter  by @marcelo-6 ([77ebdda](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/77ebdda8f491d14c3c72190f9e07443391ece75f))

- Added a test for excel2xml  by @marcelo-6 ([8aede11](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/8aede11c77707eb4c98883d9fc1a6375d1022eff))

- Add test to xml2excel  by @marcelo-6 ([1287d5f](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/1287d5fd59e42f71077b91f4013d091e13049922))


### <!-- 7 -->Miscellaneous Tasks
- Added workflows needed to publish and test  by @marcelo-6 ([1c8ecbf](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/1c8ecbf134ac7747e707f25db698f469370604e3))

- Implemented git-cliff changelog + dynamic version tooling  by @marcelo-6 ([48d346a](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/48d346a24cc7dc0d307a8391f880db5b405ac2ba))

- Added pre-commit hooks  by @marcelo-6 ([cf334cf](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/cf334cfd99725c4f6eb1c97ded8740b2a4f012ce))

- Ruff changes  by @marcelo-6 ([b0b7efe](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/b0b7efe35f2baac34b9535707a8377ca0c928b57))

- Updated gitignore  by @marcelo-6 ([4f91666](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/4f91666783ecd6a8f5a4f381514cdbd888f276c7))

- Better loggin (less bloat)  by @marcelo-6 ([aa0ce84](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/aa0ce842846cf4dfceedea7ce9faf3b4f4682c64))

- Added more detailed loggin for debug and a rotating file handler of 20MB up to 10 log files  by @marcelo-6 ([d2ba8e6](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/d2ba8e603e0b56e0d95d8964557d36659abb38fa))

- Added full recipe examples to gitignore  by @marcelo-6 ([6514c64](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/6514c6467c48d317f3381ec3b6347cfac3ebb88a))

- Uv  by @marcelo-6 ([513e540](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/513e54013c281c80895972dbf82f19b8dae92c73))


### Other
- Version 0.2.0 → 0.2.1  by @marcelo-6 ([74fd257](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/74fd257dd54071cec5587b118af12bfff454f081))

- Added new exe for this version  by @marcelo-6 ([5145552](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/5145552b714804e6799e79911c355fd3000f9109))

- Version 0.1.4 → 0.2.0  by @marcelo-6 ([7d9e77e](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/7d9e77ea29e3d470327e8e94eaa8438d01b3280c))

- Merge branch 'chore/fix' into 'master'  by @marcelo-6 ([b439fd8](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/b439fd8dc1517dd3fe5d7f0b49809498ea4bbf86))

- Add exe for this version  by @marcelo-6 ([f9910c6](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/f9910c6b088109ec3e8b6c750ec7a67647cb87d7))

- Merge branch 'chore/fix' into 'master'  by @marcelo-6 ([f919ea3](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/f919ea3c621c8b68ff2f5abfb440016044a1b745))

- Merge branch 'marcelo' into 'master'  by @marcelo-6 ([d3c0446](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/d3c04461a1cdbfd39a7e50329c6b3555257a2156))

- Gitignore fix  by @marcelo-6 ([b17a633](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/b17a633bd5223882236bdb7968663d867217a38a))

- Edit  by @marcelo-6 ([071c29f](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/071c29ffdcd7e56829f5c8f9d14de65ae34ef56d))

- Kinda fixed  by @marcelo-6 ([55d6bc1](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/55d6bc1ca7c8ec62ffac8f5292f939f104373af7))

- Revert "fixed"  by @marcelo-6 ([942464d](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/942464d442547677da2d225da3dbcb8b29628353))

- Initial Commit  by @marcelo-6 ([99e4ee7](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/99e4ee701d9a7aba4dd43ab823a9dd03cdb1897e))

- Initial Commit  by @marcelo-6 ([db811a5](https://github.com/marcelo-6/ftbatch-bulk-edit/commit/db811a5e47da9c81ef0d2d8094ebd66b827a639b))


### New Contributors
* @marcelo-6 made their first contribution

## 0.2.1 (2025-05-29)

### Feat

- **logging**: added deferrals count to output
- **logging**: added better summary for what changes were made for excel2xml
- **xml_model**: support ParamExpression in FormulaValue
- auto-size columns to fit content
- **xml_model**: insert new <Parameter> nodes in correct position
- **parser**: added proper tracker of updated parameters
- **makefile**: add Make commands, making it easier to build / prepare to build. The pyinstaller still needs to run from windows

### Fix

- **xml_model**: fixed the way ParamExpression types are represented in excel
- **parser**: added save string strip for whern the excel sheet has boolean values (FALSE) for the scale cells for example
- **xml generation**: add extended debug logging
- **xml generation**: order of new parameters creation is now pre-determined

### Refactor

- reorganized code to make it easier to troubleshoot and read

## v0.1.4 (2025-05-19)

### Feat

- **makefile**: add Make commands, making it easier to build / prepare to...

## 0.2.0 (2025-05-21)

### Fix

- **xml generation**: add extended debug logging

### Refactor

- reorganized code to make it easier to troubleshoot and read

## 0.1.4 (2025-05-19)

### Fix

- **makefile**: exe will now generate metadata correctly

## 0.1.3 (2025-05-19)

### Fix

- removed vscode settings from git

## 0.1.2 (2025-05-19)

### Feat

- **makefile**: add Make commands, making it easier to build / prepare to build. The pyinstaller still needs to run from windows

## 0.1.1 (2025-05-19)

### Fix

- **xml generation**: order of new parameters creation is now pre-determined

## 0.1.0 (2025-03-16)

### BREAKING CHANGE

- new dependencies

### Feat

- added first pass for xml2excel and excel2xml code

### Fix

- edge case for no argument
- fixed multiple file parse based on parent file
- added better logging
- better parse for a single file with complete conversion of oxml

## 0.0.2 (2025-02-08)

### Fix

- **Global**: Migrated pre-commit to latest
- **Global**: Added details to pyproject.toml along with configuration for python semantic versioning release

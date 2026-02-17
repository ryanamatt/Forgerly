## 🏷️ PR Type

- [ ] **feat**: A new feature (e.g., adding the Notes feature)
- [ ] **fix**: A bug fix (e.g., edge update lag)
- [ ] **refactor**: Moving to QFrame or improving UI consistency
- [ ] **perf**: C++ core optimizations or C-API improvements
- [ ] **docs**: Documentation updates (README, SCHEMA, etc.)
- [ ] **chore**: Updating build tasks, dependencies, tools.

## 📝 Description

## 🔗 Related Tasks

- Fixes #

### **Frontend (Python)**

- [ ] Modified `repository/` or `services/`
- [ ] Updated `ui/` views or `widgets/`

### **Core (C++ & Bridge)**

- [ ] Modified `c_lib/` (e.g., `graph_layout_engine.cpp`)
- [ ] Updated `Python C++ Wrappers` or C-API `Node`/`Edge` structs

### **Data & Schema**

- [ ] Database Schema change
- [ ] Migration of project folder structure

## ✅ Quality Checklist'

- [ ] **Unit Tests**: All tests in `tests/` pass with current changes.
- [ ] **C++ Integrity**: No memory leaks or segmentation faults in the `nf_core_lib`.
- [ ] **Python Wrapper**: Mandatory workflow followed (no raw `_clib` calls in UI).
- [ ] **Styling**: UI changes are compatible with existing `.qss` theme files.
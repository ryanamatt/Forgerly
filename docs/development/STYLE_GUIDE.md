# **Narrative Forge Coding Standards**

This document outlines the technical standards and best practices for contributing to Narrative Forge. Following these guidelines ensures consistency across the Python frontend and C++ core.

## **1\. General Principles**

* **Readability Over Brevity**: Code should be self-documenting where possible.  
* **Consistency**: Follow existing patterns in the codebase (e.g., Repository pattern for data access).  
* **Safety**: Ensure C++ memory safety and robust Python error handling.  
* **File Headers**: The first line of **every** code file (Python, C++, SQL) must be a comment indicating the file's path relative to the project root.  
  * *Python Example:* \# src/python/ui/main\_window.py  
  * *C++ Example:* // src/c\_lib/core/layout\_engine.cpp  
  * *SQL Example:* \-- src/database/schema\_v1.sql

## **2\. Python Standards (Frontend)**

The Python side uses **PySide6** and follows **PEP 8** with specific architectural constraints.

### **Naming Conventions**

* **Modules/Files**: snake\_case.py  
* **Classes**: PascalCase  
* **Functions/Methods**: snake\_case  
* **Variables**: snake\_case  
* **Constants**: UPPER\_SNAKE\_CASE

### **Architecture & Layers**

To maintain a clean separation of concerns, the project follows a strict layered architecture:

* **UI Layer (src/python/ui/)**: Only handles display and user input. No direct database or C-API calls.  
* **Service Layer (src/python/services/)**: Contains business logic. This layer coordinates between repositories and the C++ bridge.  
* **Repository Layer (src/python/repository/)**: Handles all data persistence (SQLAlchemy/SQLite).  
* **Prohibited**: Never call the raw C-API (\_clib) directly from a UI component. Use a Service or Utility wrapper.

### **Documentation (Sphinx)**

Every Python function and class **must** have a Sphinx-compliant docstring, even if the element is internal to the module.

* **Format**: Use the Sphinx/ReStructuredText format.  
* **Content**: Include descriptions for parameters (:param:), return types (:return:), and exceptions (:raises:).

### **Communication & Events**

* **Event Bus**: Use the global Event Bus for cross-component communication (e.g., notifying the Graph View that a Character was updated).  
* **PySide6 Signals**: Signals are **only** permitted for:  
  1. Connecting default widget events to internal functions (e.g., QPushButton.clicked).  
  2. Direct Parent-to-Child communication.  
* **Prohibited**: Do not use custom PySide signals to broadcast events across the application; use the Event Bus instead.

## **3\. C++ Standards (Core)**

The core library handles high-performance tasks like the Fruchterman-Reingold layout.

### **Naming Conventions**

* **Files**: snake\_case.cpp / snake\_case.h  
* **Classes**: PascalCase  
* **Functions**: snake\_case  
* **Members**: m\_variableName (m\_ prefix)

### **Documentation (Doxygen)**

All C++ code must be documented using **Doxygen** style comments.

* Use /\*\* ... \*/ blocks for classes and functions.  
* Use @param and @return tags.

## **4\. C-API Bridge & Memory Management**

The bridge between Python and C++ is a critical safety point.

* **Single Load Principle**: Never call dlopen or ffi.dlopen outside of ffi\_base.py.  
* **Allocation**: Python is responsible for allocating memory for output arrays before calling C++ functions.  
* **Ownership**: C++ objects created via \_create functions must have a corresponding \_destroy function called by the Python wrapper's destructor to prevent leaks.

## **5\. Logging & Observability (Python)**

To ensure effective debugging and crash analysis, use the centralized logging system defined in src/python/utils/logger.py.

* **No Print Statements**: Never use print() for debugging or status updates. Use the logger instead.  
* **Logger Retrieval**: Always use get\_logger(\_\_name\_\_) to ensure logs are categorized by their module.  
* **Level Usage**:  
  * DEBUG: Verbose technical info (e.g., individual C-API calls, layout iteration snapshots).  
  * INFO: General application flow (e.g., "Project Loaded", "Export Started").  
  * WARNING: Non-fatal issues (e.g., "Missing optional C-library optimization").  
  * ERROR: Critical failures (e.g., "Database connection lost", "C++ Engine Segfault").  
* **C-API Bridge**: All calls to the \_clib within wrapper classes should ideally be wrapped in try...except blocks with an ERROR log if the bridge fails.

## **6\. SQL Standards**

* **File Headers**: Must include the \-- path/to/file.sql comment on line 1\.  
* **Keywords**: Use UPPERCASE for SQL keywords (e.g., SELECT, CREATE TABLE).  
* **Naming**: Use snake\_case for table and column names.

## **7\. Testing & Quality Assurance**

* **Unit Tests**: Every new feature must include tests in the tests/ directory.  
* **Tools**: Use pytest for Python and ensure all C++ logic is exercised through Python wrapper tests.  
* **Integrity**: C++ code must be checked for memory leaks. Any PR affecting the core must verify that no segmentation faults are introduced during layout iterations.
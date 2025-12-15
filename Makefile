# --- Variables ---

# Compiler and Flags
CXX         = g++
CXXFLAGS    = -std=c++17 -Wall -Wextra -Wpedantic
LDFLAGS     = -shared
# Flags to statically link libstdc++ and libgcc
STATIC_LIBS = -Isrc/c_lib -std=c++17     -Wl,--out-implib,src/c_lib/libnf_core.a     -static-libstdc++ -static-libgcc -static

# Source and Output Paths
SRC_DIR     = src/c_lib
# List ALL C++ source files to be compiled into the single library
SRC_FILES   = $(SRC_DIR)/text_stats/text_stats_engine.cpp \
			  $(SRC_DIR)/graph_layout/graph_layout_engine.cpp \
              $(SRC_DIR)/nf_c_api.cpp
              
# New, generic library names
DLL_NAME    = nf_core_lib.dll
IMPORT_LIB  = libnf_core.a
OUTPUT_DLL  = $(SRC_DIR)/$(DLL_NAME)
OUTPUT_LIB  = $(SRC_DIR)/$(IMPORT_LIB)

# Include path for the header files. -I$(SRC_DIR) is crucial for finding 
# both text_stats_engine.h and the spell_check/ headers.
INCLUDES    = -I$(SRC_DIR)

# Linker flags specific to creating a DLL and its import library
DLL_LINK_FLAGS = -Wl,--out-implib,$(OUTPUT_LIB)

# --- Targets ---

.PHONY: all clean

# Default target: builds the DLL and import library
all: $(OUTPUT_DLL)

# Rule to compile ALL source files into the shared library (DLL)
$(OUTPUT_DLL): $(SRC_FILES)
	@echo "--- Building C Shared Library: $(DLL_NAME) ---"
	$(CXX) $(LDFLAGS) -o $@ $^ $(INCLUDES) $(CXXFLAGS) $(DLL_LINK_FLAGS) $(STATIC_LIBS)
	@echo "Successfully created: $(OUTPUT_DLL) and $(OUTPUT_LIB)"

# Clean up build artifacts
clean:
	@echo "--- Cleaning C Library build files ---"
	# Check if files exist before trying to remove them to avoid errors
	-rm -f $(OUTPUT_DLL) $(OUTPUT_LIB)
	# Also remove the old build files just in case
	-rm -f $(SRC_DIR)/text_stats_engine_lib.dll $(SRC_DIR)/libtext_stats_engine.a
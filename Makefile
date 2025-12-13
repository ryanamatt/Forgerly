# --- Variables ---

# Compiler and Flags
CXX         = g++
CXXFLAGS    = -std=c++17 -Wall -Wextra -Wpedantic
LDFLAGS     = -shared
# Flags to statically link libstdc++ and libgcc (as in your command)
STATIC_LIBS = -static-libstdc++ -static-libgcc

# Source and Output Paths
SRC_DIR     = src/c_lib
SRC_FILE    = $(SRC_DIR)/text_stats_engine.cpp
HDR_DIR     = $(SRC_DIR)
DLL_NAME    = text_stats_engine_lib.dll
IMPORT_LIB  = libtext_stats_engine.a
OUTPUT_DLL  = $(SRC_DIR)/$(DLL_NAME)
OUTPUT_LIB  = $(SRC_DIR)/$(IMPORT_LIB)

# Include path for the header file
INCLUDES    = -I$(HDR_DIR)

# Linker flags specific to creating a DLL and its import library
DLL_LINK_FLAGS = -Wl,--out-implib,$(OUTPUT_LIB)

# --- Targets ---

.PHONY: all clean

# Default target: builds the DLL and import library
all: $(OUTPUT_DLL)

# Rule to compile the source file into the shared library (DLL)
$(OUTPUT_DLL): $(SRC_FILE)
	@echo "--- Building C Shared Library: $(DLL_NAME) ---"
	$(CXX) $(LDFLAGS) -o $@ $< $(INCLUDES) $(CXXFLAGS) $(DLL_LINK_FLAGS) $(STATIC_LIBS)
	@echo "Successfully created: $(OUTPUT_DLL) and $(OUTPUT_LIB)"

# Clean up build artifacts
clean:
	@echo "--- Cleaning C Library build files ---"
	# Check if files exist before trying to remove them to avoid errors
	-rm -f $(OUTPUT_DLL) $(OUTPUT_LIB)
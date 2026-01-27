# --- Environment Detection ---
# Detect OS to set appropriate file extensions and flags
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    LIB_EXT     := .dll
    DLL_LINK_FLAGS := -Wl,--out-implib,$(SRC_DIR)/libnf_core.a
    STATIC_FLAGS   := -static-libstdc++ -static-libgcc -static
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        DETECTED_OS := macOS
        LIB_EXT := .dylib
        LDFLAGS := -dynamicLib
        STATIC_FLAGS := -fPIC
        DLL_LINK_FLAGS := 
    else
        DETECTED_OS := $(shell uname -s)
        LIB_EXT     := .so
        DLL_LINK_FLAGS := 
        # Static linking flags often differ or are unnecessary on Linux depending on the distro
        STATIC_FLAGS   := -fPIC 
    endif
endif

# --- Variables ---
CXX         = g++
CXXFLAGS    = -std=c++17 -Wall -Wextra -Wpedantic $(STATIC_FLAGS)
LDFLAGS     = -shared
SRC_DIR     = src/c_lib

# Source Files
SRC_FILES   = $(SRC_DIR)/text_stats/text_stats_engine.cpp \
              $(SRC_DIR)/graph_layout/graph_layout_engine.cpp \
              $(SRC_DIR)/spell_checker/spell_checker_engine.cpp \
              $(SRC_DIR)/nf_c_api.cpp

# Output Naming
LIB_NAME    = nf_core_lib$(LIB_EXT)
OUTPUT_LIB  = $(SRC_DIR)/$(LIB_NAME)
INCLUDES    = -I$(SRC_DIR)

# --- Targets ---
.PHONY: all clean

all: $(OUTPUT_LIB)

$(OUTPUT_LIB): $(SRC_FILES)
	@echo "--- Building for $(DETECTED_OS): $(LIB_NAME) ---"
	$(CXX) $(LDFLAGS) -o $@ $^ $(INCLUDES) $(CXXFLAGS) $(DLL_LINK_FLAGS)
	@echo "Successfully created: $(OUTPUT_LIB)"

clean:
	@echo "--- Cleaning build files ---"
	rm -f $(SRC_DIR)/*.dll $(SRC_DIR)/*.so $(SRC_DIR)/*.a $(SRC_DIR)/*.o
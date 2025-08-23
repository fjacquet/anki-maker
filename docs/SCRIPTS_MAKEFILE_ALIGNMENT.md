# Scripts and Makefile Alignment

This document describes the relationship between standalone scripts in the `scripts/` directory and Makefile targets, providing guidance on which approach to use for different tasks.

## Overview

The project uses both standalone scripts and Makefile targets for development tasks. This document clarifies their relationship and provides migration guidance to ensure consistency between local development and CI environments.

## Current State Analysis

### Scripts Directory (`scripts/`)

| Script | Purpose | Makefile Equivalent | Status | Action Taken |
|--------|---------|-------------------|--------|--------------|
| ~~`quality_check.sh`~~ | Code quality checks | `make quality` | **REMOVED** | ✅ **Deleted - functionality in Makefile** |
| `security_validation.py` | Security validation | `make security-validate` | **INTEGRATED** | ✅ **Kept - properly integrated** |
| ~~`setup_dev.sh`~~ | Development setup | `make setup-full` | **REMOVED** | ✅ **Deleted - enhanced Makefile** |
| `validate_config.py` | Configuration validation | `make validate` | **INTEGRATED** | ✅ **Kept - properly integrated** |

### Makefile Targets

The Makefile provides comprehensive targets that cover all development workflows:

#### Core Development Targets
- `make install-dev` - Install with development dependencies
- `make setup` - Set up development environment
- `make quality` - Run all quality checks
- `make test` - Run tests
- `make validate` - Validate configuration
- `make build` - Build package

#### CI-Specific Targets
- `make ci-setup` - CI environment setup
- `make ci-test` - CI-optimized testing
- `make ci-quality` - CI-optimized quality checks
- `make ci-validate` - CI configuration validation
- `make ci-build` - CI package building

## Detailed Analysis

### 1. Quality Checks

**Script**: `scripts/quality_check.sh`
**Makefile**: `make quality` and `make ci-quality`

**Comparison**:
- **Script approach**: Direct command execution without `uv run` prefix
- **Makefile approach**: Uses `uv run` prefix consistently, better error handling, CI-specific formatting

**Issues with script**:
```bash
# Script uses direct commands (problematic)
ruff check src/ --fix
mypy src/document_to_anki
bandit -r src/document_to_anki

# Makefile uses uv run (correct)
uv run ruff check --fix
uv run mypy src/document_to_anki
uv run bandit -r src/document_to_anki
```

**Recommendation**: **Remove `scripts/quality_check.sh`** and use Makefile targets exclusively.

### 2. Security Validation

**Script**: `scripts/security_validation.py`
**Makefile**: `make security-validate`

**Status**: **Properly integrated** - The Makefile target calls the script with proper `uv run` prefix.

**Makefile integration**:
```makefile
security-validate: ## Run comprehensive security validation
	@echo "Running security validation..."
	uv run python scripts/security_validation.py
```

**Recommendation**: **Keep both** - This is the correct pattern for complex scripts.

### 3. Development Setup

**Script**: `scripts/setup_dev.sh`
**Makefile**: `make setup`

**Comparison**:
- **Script**: Comprehensive setup with sample data creation and detailed output
- **Makefile**: Simple, focused setup

**Issues**:
- Script duplicates dependency installation logic
- Different approaches to environment setup
- Script creates sample documents (useful feature)

**Recommendation**: **Enhance Makefile and remove script**. Integrate useful features from script into Makefile.

### 4. Configuration Validation

**Script**: `scripts/validate_config.py`
**Makefile**: `make validate`

**Status**: **Properly integrated** - The Makefile target calls the script with proper `uv run` prefix.

**Makefile integration**:
```makefile
validate: check-env ## Validate configuration
	@echo "Validating configuration..."
	uv run python scripts/validate_config.py
```

**Recommendation**: **Keep both** - This is the correct pattern for complex validation logic.

## CI Workflow Analysis

### Current CI Usage

The CI workflow correctly uses Makefile targets:

```yaml
# Correct usage in CI
- name: Install dependencies
  run: make install-dev

- name: Run quality checks
  run: make ci-quality

- name: Test configuration validation
  run: make validate
```

### Issues Found

1. **No direct script calls in CI** ✅ - CI properly uses Makefile targets
2. **Consistent uv usage** ✅ - All CI commands go through Makefile
3. **Proper error handling** ✅ - Makefile provides CI-specific error handling

## Recommendations

### Immediate Actions

1. **Remove `scripts/quality_check.sh`**
   - Functionality completely duplicated by `make quality`
   - Script doesn't use `uv run` prefix (inconsistent)
   - CI already uses `make ci-quality`

2. **Remove `scripts/setup_dev.sh`**
   - Core functionality duplicated by `make setup`
   - Enhance Makefile with useful features from script

3. **Keep `scripts/security_validation.py`**
   - Complex logic appropriately separated
   - Properly integrated with Makefile
   - Used by both `make security-validate` and `make quality`

4. **Keep `scripts/validate_config.py`**
   - Complex validation logic appropriately separated
   - Properly integrated with Makefile
   - Used by `make validate`

### Enhanced Makefile Targets

Add missing functionality from scripts to Makefile:

```makefile
create-samples: ## Create sample documents for testing
	mkdir -p examples/sample_documents
	# Add sample document creation logic here

setup-full: setup create-samples ## Full development setup with samples
	@echo "Full development environment ready!"
```

## Best Practices

### When to Use Scripts vs Makefile

**Use Makefile targets for**:
- Simple command sequences
- Development workflow orchestration
- CI/CD pipeline steps
- Cross-platform compatibility
- Dependency management

**Use standalone scripts for**:
- Complex logic requiring programming constructs
- Extensive validation or analysis
- Reusable utilities that may be called independently
- Platform-specific operations

### Integration Pattern

When keeping scripts, always integrate them through Makefile:

```makefile
target-name: ## Description
	@echo "Running [description]..."
	uv run python scripts/script_name.py
```

**Benefits**:
- Consistent `uv run` usage
- Proper virtual environment handling
- CI/CD compatibility
- Error handling and reporting
- Documentation through `make help`

## Migration Plan

### Phase 1: Remove Duplicate Scripts ✅
- [x] Document current state
- [x] Remove `scripts/quality_check.sh`
- [x] Remove `scripts/setup_dev.sh`
- [x] Update any documentation references

### Phase 2: Enhance Makefile ✅
- [x] Add `create-samples` target
- [x] Add `setup-full` target with sample creation
- [x] Ensure all useful script functionality is preserved

### Phase 3: Validation ✅
- [x] Test all Makefile targets work correctly
- [x] Verify CI pipeline continues to work (no direct script calls found)
- [x] Update documentation

## Conclusion

The project should standardize on Makefile targets for all development workflows, with complex logic appropriately separated into standalone scripts that are called through Makefile targets. This approach provides:

1. **Consistency** - All commands use `uv run` prefix
2. **CI Compatibility** - Same commands work locally and in CI
3. **Maintainability** - Single source of truth for workflows
4. **Discoverability** - `make help` shows all available commands
5. **Error Handling** - Proper exit codes and error reporting

## Final Status ✅

**COMPLETED**: All duplicate scripts have been removed and Makefile enhanced with missing functionality.

### What Was Accomplished

1. **Removed Duplicate Scripts**:
   - `scripts/quality_check.sh` - Replaced by `make quality` and `make ci-quality`
   - `scripts/setup_dev.sh` - Replaced by enhanced `make setup` and new `make setup-full`

2. **Enhanced Makefile**:
   - Added `create-samples` target for sample document creation
   - Added `setup-full` target for comprehensive development setup
   - Preserved all useful functionality from removed scripts

3. **Maintained Proper Integration**:
   - `scripts/security_validation.py` - Properly called by `make security-validate`
   - `scripts/validate_config.py` - Properly called by `make validate`

4. **Verified CI Compatibility**:
   - No direct script calls in CI workflow
   - All CI commands use Makefile targets
   - Consistent `uv run` usage throughout

### Current Architecture

The project now follows the recommended pattern:
- **Makefile targets** for all development workflows
- **Standalone scripts** only for complex logic that requires programming constructs
- **Proper integration** where scripts are called through Makefile with `uv run` prefix
- **CI compatibility** with identical commands between local and CI environments

This provides consistency, maintainability, and a single source of truth for all development operations.
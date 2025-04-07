# TODO Tasks

## Test Dataset Integration
**Priority**: Medium
**Status**: Pending
**Created**: April 2024

### Description
Create test cases and integration tests using the downloaded test datasets (Guerry and Iris).

### Datasets Available
1. `tests/data/guerry.csv`: Social indicators from 1830s France
   - Good for: correlation analysis, complex statistics, social science data
2. `tests/data/iris.csv`: Flower measurements dataset
   - Good for: basic statistics, classification, visualization

### Tasks
- [ ] Create test cases using both datasets
- [ ] Test loading datasets in web application
- [ ] Create example analyses for documentation
- [ ] Add visualization tests
- [ ] Test statistical analysis features

### Implementation Notes
- Datasets are located in `tests/data/`
- Download script available at `tests/download_test_data.py`
- Consider both basic and advanced statistical analyses
- Include visualization testing

### Related Files
- `tests/download_test_data.py`
- `tests/data/guerry.csv`
- `tests/data/iris.csv` 
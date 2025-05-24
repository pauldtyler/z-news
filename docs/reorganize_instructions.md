# Notebook Reorganization Instructions

Follow these steps to reorganize your notebook for a logical workflow:

## 1. Keep Introduction and Setup Cells (Cells 0-4)
- Cell 0: Introduction markdown
- Cell 1: Import libraries with dotenv
- Cell 2: Client list definition
- Cell 3: Search function
- Cell 4: Main search for first batch of clients

## 2. Client Data Collection Section

### Core Data Collection (First Section)
- Keep Cell 5: Converting results to DataFrame
- Keep Cell 13: Save CSV data (move to after cell 5)
- Add Cell 10: Search different client ranges
- Add Cell 12: Adaptive search for different client profiles

### Claude API Integration (Second Section)
- Add Cell 19: Function to prepare data for Claude API
- Add Cell 15: Function to call Claude API with .env file
- Add Cell 18: All-in-one pipeline function

### Analysis and Visualization (Final Section)
- Move Cell 8: Basic analysis functions 
- Move Cell 9: Visualization of articles by company
- Move Cell 11: Article frequency by time period
- Keep instructions at the end (Cells 16-17)

## Tips for Manual Rearrangement in Jupyter
1. In Jupyter, click on a cell to select it
2. Use the up/down arrow buttons in the toolbar to move it
3. Alternatively, use the Cell menu > Move Cell Up/Down
4. You can also cut a cell with Ctrl+X (or Cmd+X on Mac) and paste it elsewhere with Ctrl+V (or Cmd+V)

## End Result Order Should Be
1. Introduction & Setup
2. News Collection (search, DataFrame conversion, CSV save)
3. Claude API Integration
4. Analysis & Visualization
5. Instructions

This rearrangement will make the notebook flow in a more logical sequence to match your requirements.
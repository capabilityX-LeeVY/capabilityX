**SYSTEM:**

You will be provided with a control table from a **Meeting Scenario**. Your task is to perform the following actions to ensure data accuracy:

### Step 1: Query and Format the Table

1. **Extract Relevant Columns:**
   - Extract and display only the **Control** and **Compliance** columns from the provided table.
   - Ensure that the extracted table contains only these two columns and no additional content or rows.

2. **Check and Correct Formatting:**
   - Verify that the **Compliance** column contains only the following values:
     - `✅ Compliant`
     - `❌ Non-compliant`
   - Ensure there are no discrepancies or extra entries. Correct any formatting issues so that all entries match the specified values.

### Step 2: Perform Calculations Based on the Extracted Table

1. **Total Controls Number:**
   - Count the total number of rows in the extracted table.

2. **Compliant Controls Number:**
   - Count the number of rows where the **Compliance** column is marked as `✅ Compliant`.
   - Ensure that only the rows within the table are counted. Do not include any entries outside of this table.

3. **Non-compliant Controls Number:**
   - Count the number of rows where the **Compliance** column is marked as `❌ Non-compliant`.
   - Ensure that only the rows within the table are counted. Do not include any entries outside of this table.

4. **Accessibility Score Calculation:**
   - Use the following formula to calculate the Accessibility Score:
     - **Penalty**: 10 points
     - **Accessibility Score** = `100 - ((Non-compliant Controls Number / Total Controls Number) × 100) - Penalty`

### Step 3: Generate Results

1. **Overall Summary:**
   - Generate an overall summary based on the results of the calculations.

2. **Control Compliance Overview Table:**
   - Create a summary table showing the total controls, compliant controls, non-compliant controls, and the calculated accessibility score.

---

### Overall Summary:

| **Category**                | **Count**               | **Percentage** | **Score**               | **Penalty**           |
|-----------------------------|-------------------------|----------------|-------------------------|-----------------------|
| Total Controls Evaluated     |    | -              | -                       | -                     |
| Compliant Controls           | |             | -                       | -                     |
| Non-compliant Controls       |  |         | -                       | -                     |
| Accessibility Score          | -                       | -              |       |                    |

---

**USER:**

- **Meeting Scenario**: `{test_scenario}`


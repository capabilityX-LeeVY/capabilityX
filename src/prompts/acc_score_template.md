## What is an accessibility score?

An accessibility score is a measure of how well a application conforms to accessibility guidelines and best practices. It takes into account factors such as description clariy, easy to navigate, and much more. The score is represented as a number between 0 and 100, with higher scores indicating better accessibility.

Accessibility scores are calculated based on compliance with the Web Content Accessibility Guidelines (WCAG) 2.2 accessibility standard. This standard is widely recognized and accepted as the benchmark for accessibility.

## Why is an accessibility score important?

Accessibility scores provide a quick and easy way to assess the accessibility of application, and help you monitor the accessibility of application and ensure that everyone, regardless of their abilities, can use it. Without good accessibility, these individuals may struggle to navigate your application or may not be able to access it at all.

Achieving a higher accessibility score not only makes your application more inclusive but also offers additional benefits. It enhances user experience (UX), design, and content usability. Furthermore, it can provide high-quality, structured datasets for self-learning and enable AI-driven automation through self-directed planning and action.

## How is an accessibility score calculated?

To calculate the Accessibility Score, penalties for non-compliance are assigned based on the WCAG level of the violation. Here is a proposed penalty system:

Here is the translation:

---

### Theories and Principles:

1. **Weighted Scoring Theory**:
   - This method assigns different penalty weights to different WCAG levels, reflecting the importance of compliance requirements for overall accessibility. Generally, WCAG Level A standards are the most basic requirements, and violations of these standards have a greater impact, so their penalty weight is set higher.

2. **Maximum Penalty Theory**:
   - Setting the maximum penalty as the total number of controls multiplied by the highest penalty weight ensures that even the most severe violations will have a significant impact on the overall score. This approach helps prevent scores from becoming too lenient, ensuring that severe violations are effectively quantified.

3. **Scoring Calculation Formula**:
   - The formula for calculating the total penalty is based on the number of violations at different levels and their corresponding penalty weights. This weighted approach reflects the differential treatment of violations at various levels.
   - The final accessibility score calculation formula compares the total penalty with the maximum possible penalty to generate a percentage score. This method quantifies non-compliance into an easily understandable score, reflecting the accessibility status of the entire system.

These theories ensure that the scoring system accurately reflects the severity of accessibility issues at different levels while also ensuring fairness and reasonableness in the evaluation results.

### What Is AAA Accessibility Rating?

WCAG’s success criteria are organized by three levels of conformance: Level A, Level AA, and Level AAA. 

   - **Level A** includes issues with the greatest potential impact on real-life users. For example, WCAG 2.0/2.1 Level A prohibits keyboard traps, which prevent keyboard users from navigating content.
   - **Level AA** includes all Level A criteria, along with additional requirements that could impact users. For example, WCAG 2.2 Level AA includes requirements for color contrast.
   - **Level AAA** includes both Level A and Level AA criteria and includes additional criteria that improve accessibility for users with disabilities. Level AAA is the most strict conformance level and is nearly impossible to meet. 

### Approach: Weighted Impact & Normalized Penalties

Instead of subtracting a flat penalty from the score, we can use a **weighted penalty system** based on the severity of the violation (Level A, AA, AAA) and normalize the penalties in a way that better reflects the distribution of compliant vs. non-compliant controls.

### Step-by-Step Process

1. **Penalty Weights**: Assign weighted penalties to each WCAG level:

   Here are brief comments for each WCAG level in the table:

   ---

   | **WCAG Level** | **Penalty Weight (Points per Violation)** | **Comments**                                                   |
   |----------------|-------------------------------------------|---------------------------------------------------------------|
   | Level A        | 3                                         | **Basic Accessibility**: Fundamental requirements to ensure essential content is accessible to all users. Missing these can significantly impact usability. |
   | Level AA       | 2                                         | **Enhanced Accessibility**: Addresses more advanced barriers to improve user experience and access for a broader range of disabilities. |
   | Level AAA      | 1                                         | **Optimal Accessibility**: Highest level of accessibility, focusing on the most comprehensive user needs. Compliance can be challenging but provides the most inclusive experience. |

   ---

2. **Calculate Maximum Possible Penalty**: 
   The maximum possible penalty is the total number of controls multiplied by the highest penalty weight (Level A’s 3 points). This prevents scores from going to zero too easily while ensuring that severe violations still have a major impact.

   $$
   \text{Maximum Possible Penalty} = \text{Total Controls} \times \text{Penalty Weight for Level A}
   $$

3. **Total Penalty Formula**:

   $$
   Total \, Penalty = (Level \, A \, Non-compliance \times 3) + (Level \, AA \, Non-compliance \times 2) + (Level \, AAA \, Non-compliance \times 1)
   $$


4. **Accessibility Score Formula**:

   $$
   \text{Accessibility Score} = 100 \times \left(1 - \frac{\text{Total Penalty}}{\text{Maximum Possible Penalty}}\right)
   $$

### Example Calculation

**Input**

| **Category**             | **Count** | **Percentage** | **Score(100)** | **Penalty/Maximum Penalty**     |
|--------------------------|-----------|----------------|----------------|-----------------|
| Total Controls           |     100   |                |       -        |     -           |
| Compliant Controls       |     80    |       %        |       -        |     -           |
| Non-compliant(Level A)   |     10    |       %        |       -        |     %           |
| Non-compliant(Level AA)  |     8     |       %        |       -        |     %           |
| Non-compliant(Level AAA) |     2     |       %        |       -        |     %           |
| Accessibility Score      |     -     |       -        |                |     %           |

Let’s revisit the example where we have:
- **Total controls**: 100
- **Non-compliant controls**: 20
  - **Level A violations**: 10
  - **Level AA violations**: 8
  - **Level AAA violations**: 2

1. **Calculate Penalties**:
   - **Level A penalty**: 10 violations × 3 points = 30
   - **Level AA penalty**: 8 violations × 2 points = 16
   - **Level AAA penalty**: 2 violations × 1 point = 2

2. **Total Penalty**: 
   
   $$
   \text{Total Penalty} = (\text{Level A Penalty}) + (\text{Level AA Penalty}) + (\text{Level AAA Penalty}) = 30 + 16 + 2 = 48
   $$

3. **Maximum Possible Penalty**: 
   
   $$
   \text{Maximum Possible Penalty} = \text{Total Controls} \times \text{Penalty Weight for Level A} = 100 \times 3 = 300
   $$

4. **Accessibility Score**:
   
   $$
   \text{Accessibility Score} = 100 \times \left(1 - \frac{48}{300}\right) = 100 \times (1 - 0.16) = 100 \times 0.84 = 84
   $$

**Output**

| **Category**             | **Count** | **Percentage** | **Score (100)** | **Penalty/Maximum Penalty** |
|--------------------------|-----------|----------------|-----------------|-----------------------------|
| Total Controls           |     100   |        -       |        -        |             -               |
| Compliant Controls       |     80    |       80%      |        -        |             -               |
| Non-compliant(Level A)   |     10    |       10%      |        -        |            10%              |
| Non-compliant(Level AA)  |     8     |        8%      |        -        |          5.33%              |
| Non-compliant(Level AAA) |     2     |        2%      |        -        |          0.67%              |
| Accessibility Score      |     -     |        -       |       84        |          16%                |

Here's an interpretation of the **Accessibility Score** to provide a clear understanding of what the score means for the overall user experience and compliance with accessibility standards:

### **Accessibility Score Interpretation**

| **Score Range**  | **Rating**               | **Interpretation**                                                                                                                                                 |
|------------------|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **100 - 90**     | **Excellent accessibility** | The application meets most, if not all, accessibility standards. Very few or no barriers exist for users with disabilities. Minor improvements, if any, are needed. |
| **89 - 70**      | **Good accessibility**     | The application is largely accessible, but there are some issues that may affect certain users. These should be addressed to ensure a more inclusive experience.    |
| **69 - 50**      | **Moderate accessibility concerns** | Several areas have accessibility problems that could affect many users, particularly those with disabilities. Improvements are required to prevent exclusion.       |
| **49 or below**  | **Serious accessibility issues** | Key functionalities are likely inaccessible to a large portion of users. Immediate action is needed to make the application usable for people with disabilities.     |

### **Explanation of Each Score Range**:

1. **100 - 90: Excellent Accessibility**
   - The application is almost entirely compliant with accessibility standards. It provides an inclusive experience for all users, including those who rely on assistive technologies.
   - **Actions**: Minor improvements might be considered for optimization, but overall, the app is accessible.

2. **89 - 70: Good Accessibility**
   - While the application is largely accessible, there are specific issues that could create barriers for some users. These issues may not be critical but could affect the usability for people with certain disabilities.
   - **Actions**: Address the noted issues to improve accessibility and user experience.

3. **69 - 50: Moderate Accessibility Concerns**
   - Accessibility issues are noticeable and may affect a significant portion of users, particularly those who depend on assistive technologies.
   - **Actions**: A review of the application is needed, with targeted fixes for critical accessibility problems to improve inclusivity.

4. **49 or Below: Serious Accessibility Issues**
   - Major barriers exist that prevent users with disabilities from interacting with key functions of the application. This score indicates non-compliance with accessibility standards, which can result in legal risks and exclusion of a significant number of users.
   - **Actions**: Immediate corrective action is required to address critical barriers and make the application usable for all users, including those with disabilities.


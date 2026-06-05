

# Retirement Calculator Web App

A sleek, static HTML retirement planning dashboard that helps users explore time value of money, long-term savings growth, withdrawal scenarios, and inflation-adjusted retirement expenses.

This project was built as a lightweight front-end web application using HTML, CSS, JavaScript, and Chart.js. It is designed to run directly in the browser without a backend, database, or login system.

## Project Overview

The Retirement Calculator Web App allows users to model different retirement planning scenarios using interactive inputs and dynamic charts. The goal of the project is to provide a clean, modern, and easy-to-understand financial planning interface that can be deployed as a simple static website.

The current version includes:

* A dashboard overview of projected retirement value
* A time value of money calculator
* A 40-year retirement projection model
* Editable annual contribution schedule
* Conservative, base, and aggressive return scenarios
* Adjustable scenario return assumptions
* Withdrawal rule analysis
* Inflation-adjusted retirement expense projection
* Retirement income gap or surplus analysis
* Goal tracking and progress indicators
* Dark, modern financial dashboard design

## Live Demo

A live version of this project can be deployed using Netlify, Vercel, or GitHub Pages.

Example deployment platforms:

* Netlify
* Vercel
* GitHub Pages

## Technologies Used

* HTML5
* CSS3
* JavaScript
* Chart.js
* Python

The Python script generates the final static HTML file. The deployed website itself runs entirely in the browser.

## File Structure

```text
retirement-calculator/
│
├── build_retirement_calculator_v2.py
├── index.html
└── README.md
```

## Main Features

### Dashboard

The dashboard provides a high-level retirement planning summary, including:

* Estimated future portfolio value
* Monthly contribution
* Expected annual return
* Savings rate
* Safe withdrawal estimate
* Inflation-adjusted expense estimate
* Retirement income gap or surplus

### Time Value of Money Calculator

The TVM calculator allows users to enter:

* Present value
* Monthly payment
* Annual rate of return
* Number of months

The app then calculates a future value and displays a growth curve.

### 40-Year Projection

The 40-year projection tab allows users to model long-term retirement savings using a year-by-year contribution schedule.

Users can adjust:

* Annual contribution amounts
* Conservative return assumption
* Base return assumption
* Aggressive return assumption
* Target portfolio goal
* Nominal versus inflation-adjusted display

### Withdrawal Analysis

The withdrawal tab shows estimated annual and monthly income under different withdrawal rules, including:

* 3.0%
* 3.5%
* 4.0%
* 4.5%
* 5.0%

### Inflation and Expenses

The inflation tab allows users to estimate how current expenses may grow by retirement using an annual inflation assumption.

For example, a user can input current annual expenses and apply a 3% inflation escalator to estimate future retirement expenses.

### Scenario Testing

The scenario tab allows users to compare different planning outcomes, including:

* Base case
* Delayed retirement
* Higher savings
* Lower return stress test

## How to Run Locally

1. Clone or download the project folder.

2. Run the Python script:

```bash
python build_retirement_calculator_v2.py
```

3. The script will generate an HTML file:

```text
Retirement Calculator v2.html
```

4. Rename the file to:

```text
index.html
```

5. Open `index.html` in your browser.

## How to Deploy

This project can be deployed as a static website.

### Option 1: Netlify

1. Create a folder called:

```text
RetirementCalculatorSite
```

2. Place the `index.html` file inside the folder.

3. Go to Netlify.

4. Sign in and use the manual deploy / drag-and-drop option.

5. Drag the full folder into Netlify.

6. Netlify will provide a public website URL.

### Option 2: GitHub Pages

1. Create a GitHub repository.

2. Upload the project files.

3. Make sure the main HTML file is named:

```text
index.html
```

4. Enable GitHub Pages in the repository settings.

5. GitHub will provide a public website URL.

### Option 3: Vercel

1. Create a GitHub repository.

2. Upload the project files.

3. Connect the repository to Vercel.

4. Deploy the project.

## Future Enhancements

Potential future versions could include:

* Monte Carlo retirement simulation
* User login and saved scenarios
* Database-backed user profiles
* Account-level portfolio assumptions
* PDF export
* CSV export
* Mobile-first redesign
* Tax-adjusted retirement income modeling
* Roth versus traditional account modeling
* Social Security estimate inputs
* Required minimum distribution modeling
* Asset allocation assumptions
* Historical market return backtesting
* Probability of success analysis
* Integration with a backend API

## Future Full-Stack Architecture

A future full-stack version could use:

* Frontend: React or Next.js
* Hosting: Vercel or Netlify
* Authentication: Supabase Auth, Firebase Auth, Clerk, or Auth0
* Database: Supabase Postgres or Firebase
* Backend: Next.js API routes, FastAPI, or serverless functions
* Payments: Stripe, if monetized

## Disclaimer

This application is for educational and illustrative purposes only. It does not provide investment, tax, legal, or financial advice. Retirement projections are hypothetical and depend on user assumptions, market performance, inflation, taxes, and personal financial circumstances.



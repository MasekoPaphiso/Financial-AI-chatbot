import pandas as pd

RESPONSE_TEMPLATES = {
'revenue_year':
    "{company}'s {year} revenue: ${value:,.0f} million",

'compare_metric':
    "{company1} vs {company2} ({metric}):\n"
    "-{company1}: ${value1:,.0f} million\n"
    "-{company2}: ${value2:,.0f} million",

'compare_metric_year':
    "{company1} vs {company2} ({metric}, {year}):\n"
    "-{company1}: ${value1:,.0f} million\n"
    "-{company2}: ${value2:,.0f} million",

'metric_growth':
    "{company}'s {metric} growth ({year1}-{year2}):\n"
    "-{year1}: ${value1:,.0f} million\n"
    "-{year2}: ${value2:,.0f} million\n"
    "Growth: {change:+.1f}%",

'list_companies':
    "Available companies: {companies}",

'profit_margin':
    "{company}'s {year} net profit margin:\n"
    "-Net Income: ${net_income:,.0f} million\n"
    "-Total Revenue: ${revenue:,.0f} million\n"
    "Margin: {margin:.1f}%",

'avg_revenue':
    "Average revenue ({year}): ${value:,.0f} million",

'exit':
    "Thank you for using FinancialBot!",

'unknown':
    "I didn't understand that. Try:\n"
    "- 'Show Microsoft revenue for 2024'\n"
    "- 'Compare revenue between Tesla and Apple'\n"
    "- 'List all companies'"
}
def load_data():
    df = pd.read_csv('/Users/paphisomaseko/Downloads/10k company metrics.csv')
    numeric_cols = ['Total Revenue', 'Net Income', 'Total Assets', 'Total Liabilities', 'Cash Flow']
    df[numeric_cols] = df[numeric_cols].replace(r'[,\s]', '', regex=True).astype(float)
    df = df.sort_values(['Company', 'Year'])
    df['Revenue Growth (%)'] = df.groupby('Company')['Total Revenue'].pct_change() * 100
    df['Net Income Growth (%)'] = df.groupby('Company')['Net Income'].pct_change() * 100
    return df


class FinancialChatbot:
    def __init__(self, df):
        self.df = df
        self.companies = df['Company'].unique()

    def handle_query(self, query):
        query = query.lower()
        if 'exit' in query: return RESPONSE_TEMPLATES['exit']
        if 'list' in query: return self.handle_list_companies()
        if 'show' in query: return self.handle_revenue_query(query)
        if 'compare' in query: return self.handle_comparison(query)
        if 'growth' in query: return self.handle_growth_query(query)
        if 'profit margin' in query: return self.handle_profit_margin(query)
        return RESPONSE_TEMPLATES['unknown']

    def handle_revenue_query(self, query):
        parts = query.split()
        company = self.extract_company(parts)
        year = self.extract_year(parts)

        if company and year:
            value = self.df[(self.df['Company'] == company) &
                            (self.df['Year'] == year)]['Total Revenue'].values[0]
            return RESPONSE_TEMPLATES['revenue_year'].format(
                company=company, year=year, value=value
            )
        return RESPONSE_TEMPLATES['unknown']

    def handle_comparison(self, query):
        parts = query.split()
        metric = self.extract_metric(parts)
        companies = [p for p in parts if p.capitalize() in self.companies]

        if len(companies) >= 2 and metric:
            company1, company2 = companies[:2]
            year = self.extract_year(parts) or self.df['Year'].max()

            value1 = self.get_metric(company1, year, metric)
            value2 = self.get_metric(company2, year, metric)

            return RESPONSE_TEMPLATES['compare_metric'].format(
                company1=company1, company2=company2,
                metric=metric, value1=value1, value2=value2
            )
        return RESPONSE_TEMPLATES['unknown']

    def handle_growth_query(self, query):
        parts = query.split()
        company = self.extract_company(parts)
        metric = self.extract_metric(parts)
        years = [int(p) for p in parts if p.isdigit() and int(p) in self.df['Year'].unique()]

        if company and metric and len(years) == 2:
            year1, year2 = sorted(years)
            try:
                val1 = self.get_metric(company, year1, metric)
                val2 = self.get_metric(company, year2, metric)
                change = ((val2 - val1) / val1) * 100 if val1 != 0 else 0
                return RESPONSE_TEMPLATES['metric_growth'].format(
                    company=company, metric=metric,
                    year1=year1, year2=year2,
                    value1=val1, value2=val2, change=change  # Add value1/value2
                )
            except ValueError as e:
                return f"Error: {str(e)}"
        return RESPONSE_TEMPLATES['unknown']

    def handle_profit_margin(self, query):
        parts = query.split()
        company = self.extract_company(parts)
        year = self.extract_year(parts) or self.df['Year'].max()  # Default to latest year

        if company and year:
            try:
                revenue = self.get_metric(company, year, 'Revenue')
                income = self.get_metric(company, year, 'Income')
                margin = (income / revenue) * 100 if revenue != 0 else 0
                return RESPONSE_TEMPLATES['profit_margin'].format(
                    company=company, year=year,
                    net_income=income, revenue=revenue, margin=margin
                )
            except ValueError as e:
                return f"Error: {str(e)}"
        return RESPONSE_TEMPLATES['unknown']

    def extract_company(self, parts):
        for p in parts:
            if p.capitalize() in self.companies:
                return p.capitalize()
        return None

    def extract_year(self, parts):
        for p in parts:
            if p.isdigit() and int(p) in self.df['Year'].unique():
                return int(p)
        return None

    def extract_metric(self, parts):
        metrics = ['revenue', 'income']
        for p in parts:
            if p in metrics:
                return p.capitalize()
        return None

    def get_metric(self, company, year, metric):
        metric_map = {
            'Revenue': 'Total Revenue',
            'Income': 'Net Income'
        }
        return self.df[(self.df['Company'] == company) &
                       (self.df['Year'] == year)][metric_map[metric]].values[0]

    def calculate_growth(self, company, metric, year1, year2):
        metric_map = {
            'Revenue': 'Total Revenue',
            'Income': 'Net Income'
        }
        val1 = self.df[(self.df['Company'] == company) &
                       (self.df['Year'] == year1)][metric_map[metric]].values[0]
        val2 = self.df[(self.df['Company'] == company) &
                       (self.df['Year'] == year2)][metric_map[metric]].values[0]
        return ((val2 - val1) / val1) * 100 if val1 != 0 else 0

    def handle_list_companies(self):
        return RESPONSE_TEMPLATES['list_companies'].format(
            companies=', '.join(self.companies)
        )

def main():
    df = load_data()
    bot = FinancialChatbot(df)
    print(" Hi This is the Financial Analysis Chatbot\nType 'exit' to quit")
    while True:
        try:
            query = input("\nYou: ")
            response = bot.handle_query(query)
            print(f"Bot: {response}")
            if response == RESPONSE_TEMPLATES['exit']: break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
'''
Contains data and functions related to country capitals.
Provides information about China's capital and other major capitals.
'''
class CapitalFacts:
    """Class containing facts about various country capitals."""
    def __init__(self):
        """Initialize the capital facts database."""
        self.capitals = {
            'China': {
                'name': 'Beijing',
                'chinese_name': '北京',
                'population': '21.54 million',
                'area': '16,410 km²',
                'established': '1045 BC',
                'facts': [
                    'Beijing is the political, cultural, and educational center of China',
                    'It hosted the 2008 Summer Olympics',
                    'Home to the Forbidden City and the Great Wall of China',
                    'One of the Four Great Ancient Capitals of China'
                ]
            },
            'United States': {
                'name': 'Washington D.C.',
                'population': '689,545',
                'area': '177 km²',
                'established': '1790'
            },
            'Japan': {
                'name': 'Tokyo',
                'population': '13.96 million',
                'area': '2,194 km²',
                'established': '1868'
            },
            'France': {
                'name': 'Paris',
                'population': '2.16 million',
                'area': '105.4 km²',
                'established': '3rd century BC'
            }
        }
    def get_china_capital_info(self):
        """Get detailed information about China's capital."""
        china_info = self.capitals['China']
        return {
            'country': 'China',
            'capital': china_info['name'],
            'chinese_name': china_info['chinese_name'],
            'population': china_info['population'],
            'area': china_info['area'],
            'established': china_info['established'],
            'facts': china_info['facts']
        }
    def get_all_capitals(self):
        """Get a list of all capitals in the database."""
        result = []
        for country, info in self.capitals.items():
            result.append({
                'country': country,
                'capital': info['name'],
                'population': info.get('population', 'N/A'),
                'area': info.get('area', 'N/A')
            })
        return result
    def search_capital(self, country_name):
        """Search for a capital by country name."""
        country_name = country_name.title()
        if country_name in self.capitals:
            return self.capitals[country_name]
        return None
    def get_answer_to_question(self):
        """Get the direct answer to the user's question."""
        china_info = self.capitals['China']
        return f"中国的首都是{china_info['chinese_name']} ({china_info['name']})"
'''
Core module containing the answer data for the capital of China.
Provides a clean interface to retrieve the answer.
'''
class CapitalFinder:
    """Class to provide information about the capital of China."""
    def __init__(self):
        """Initialize with the answer data."""
        self.country = "中国"
        self.capital = "北京"
        self.english_country = "China"
        self.english_capital = "Beijing"
        self.additional_info = {
            "population": "约2154万人 (2020年)",
            "area": "16410.54平方公里",
            "established_as_capital": "1949年",
            "famous_landmarks": ["天安门", "故宫", "长城", "颐和园"]
        }
    def get_answer(self, language="chinese"):
        """
        Get the answer in the specified language.
        Args:
            language (str): 'chinese' or 'english' (case-insensitive)
        Returns:
            str: The answer to the question
        """
        if language.lower() == "english":
            return f"The capital of {self.english_country} is {self.english_capital}."
        else:
            return f"{self.country}的首都是{self.capital}。"
    def get_detailed_info(self):
        """
        Get detailed information about Beijing.
        Returns:
            dict: Detailed information about Beijing
        """
        return {
            "country": self.country,
            "capital": self.capital,
            "english_country": self.english_country,
            "english_capital": self.english_capital,
            "additional_info": self.additional_info
        }
    def get_fun_facts(self):
        """
        Get some interesting facts about Beijing.
        Returns:
            list: List of fun facts
        """
        return [
            "北京是中国的政治、文化、国际交往和科技创新中心。",
            "北京有着3000多年的建城史和860多年的建都史。",
            "北京是历史上五代王朝的都城。",
            "北京是2022年冬季奥运会的主办城市。",
            "北京故宫是世界上现存规模最大、保存最为完整的木质结构古建筑群。"
        ]
def create_capital_finder():
    """Factory function to create a CapitalFinder instance."""
    return CapitalFinder()
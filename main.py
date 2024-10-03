"""This program obtains a users name, and greets them.

It then provides a menu of options to choose from.

It fetches location, latitude, and longitude data based on zipcodes.
"""


import pgeocode
import math
import requests
import json


request_url = "https://archive-api.open-meteo.com/v1/archive"


def create_dataset():
    """Create a dataset of zip codes."""
    zip_code = input("Please enter a zip code: ")
    try:
        dataset = HistoricalTemps(zip_code)
        return dataset
    except LookupError:
        print("Error: The entered zip code is invalid. Please try again.")
        return None


class HistoricalTemps:
    """
    A class representing historical temperature data.

    Attributes:
        _zip_code (str): Zip code for which temperature data is fetched.
        _start (str): Start date of range for temperature data.
        _end (str): End date of range for historical temperature data.
        _temp_list (list): List of tuples containing date and temp data.
    """

    def __init__(self, zip_code, start="1950-08-13", end="2023-08-25"):
        """
        Make all necessary attributes for the HistoricalTemps object.

        Parameters:
            zip_code (str): Zip code for which to fetch temp data.
            start (str): Start date of the range.
            end (str): End date of the range.
        """
        self._zip_code = zip_code
        self._start = start
        self._end = end

        lat, lon, loc_name = self.zip_to_loc_info(zip_code)

        if math.isnan(lat) or math.isnan(lon):
            raise LookupError("Invalid zip code: Location not found")

        self._lat = lat
        self._lon = lon
        self._loc_name = loc_name

        self._temp_list = None
        self._load_temps()

    def _load_temps(self):
        """
        Load historical temperature data.

        Currently, this method is hardcoded to provide sample data.
        In the future, it will fetch real data from the internet.

        This fake data is kept for now to ensure testing is smooth.
        """
        params = {
            "latitude": self._lat,
            "longitude": self._lon,
            "start_date": self._start,
            "end_date": self._end,
            "daily": "temperature_2m_max",
            "timezone": "America/Los_Angeles"
        }

        response = requests.get(request_url, params=params)
        json_data = response.text
        self._temp_list = self._convert_json_to_list(json_data)

    def average_temp(self):
        """
        Calculate the average temperature from the loaded data.

        Returns:
            float: The average temperature.
        """
        total_temp = sum(temp for date, temp in self._temp_list)
        avg_temp = total_temp / len(self._temp_list)
        return avg_temp

    def is_data_loaded(self):
        """
        Check if temperature data is loaded.

        Returns:
            bool: True if data is loaded, False otherwise.
        """
        return self._temp_list is not None

    @property
    def zip_code(self):
        """
        Gets the zip code.

        Returns:
            str: Zip code for which temperature data is fetched.
        """
        return self._zip_code

    @property
    def start(self):
        """
        Get the start value.

        Returns:
            The start value.
        """
        return self._start

    @start.setter
    def start(self, value):
        old_start = self._start
        self._start = value
        try:
            self._load_temps()
        except Exception as e:
            self._start = old_start
            raise LookupError(f"Can't load data for start date {value}: {e}")

    @property
    def end(self):
        """
        Get the end value.

        Returns:
            The end value.
        """
        return self._end

    @end.setter
    def end(self, value):
        old_end = self._end
        self._end = value
        try:
            self._load_temps()
        except Exception as e:
            self._end = old_end
            raise LookupError(f"Can't load data for end date {value}: {e}")

    @property
    def loc_name(self):
        """
        Get the location name.

        Returns:
            str: Name of the location based on zip code.
        """
        return self._loc_name

    @staticmethod
    def zip_to_loc_info(zip_code):
        """
        Return latitude, longitude, and location name for a zip code.

        Parameters:
            zip_code (str): Zip code to look up.

        Returns:
            tuple: (latitude, longitude, location name)
        """
        nomi = pgeocode.Nominatim('us')
        location = nomi.query_postal_code(zip_code)

        if location.empty:
            return None, None, None

        lat = location.latitude
        lon = location.longitude
        loc_name = location.place_name

        return lat, lon, loc_name

    @staticmethod
    def _convert_json_to_list(data):
        """
        Convert JSON data to a list of tuples with dates and temps.

        Parameters:
            data (str): JSON string from open-meteo.com.

        Returns:
            list: List of tuples, each tuple has a date and a max temp.
        """
        data_dict = json.loads(data)
        dates = data_dict['daily']['time']
        temps = data_dict['daily']['temperature_2m_max']
        return list(zip(dates, temps))

    def extreme_days(self, threshold: float):
        """
        Find days when the temperature exceeds the given threshold.

        Parameters:
            threshold (float): The temp threshold to compare against.

        Returns:
            list: A list of tuples where the temp exceeds the threshold.
        """
        return [(date, temp) for date, temp in self._temp_list if
                temp > threshold]

    def top_x_days(self, num_days=10):
        """
        Return a list of tuples representing the days with the highest temps.

        Parameters:
            num_days (int): The number of days to return. Default is 10.

        Returns:
            list: A list of tuples (date, temp) with the highest temps.
        """
        return sorted(self._temp_list, key=lambda x: x[1], reverse=True)[
               :num_days]


def print_extreme_days(dataset: HistoricalTemps):
    """
    Print days when the temp exceeds a threshold for a given dataset.

    Parameters:
        dataset (HistoricalTemps): The temperature dataset to analyze.
    """
    if not dataset.is_data_loaded():
        print("The dataset is not loaded.")
        return

    try:
        threshold = float(input("Enter a threshold temperature: "))
    except ValueError:
        print("Please enter a valid number for the threshold temperature.")
        return

    extreme_days_list = dataset.extreme_days(threshold)

    print(
        f"There are {len(extreme_days_list)} days when"
        f" the temperature exceeded {threshold:.1f} degrees.")

    for date, temp in extreme_days_list:
        print(f"Date: {date}, Temperature: {temp:.1f} degrees")


def print_top_five_days(dataset: HistoricalTemps):
    """
    Print the top five days with the highest temps from the dataset.

    Parameters:
        dataset (HistoricalTemps): The dataset to analyze.
    """
    if not dataset.is_data_loaded():
        print("The temperature data is not loaded. Please check dataset.")
        return

    top_days = dataset.top_x_days(num_days=5)

    print(f"Top 5 hottest days for {dataset.loc_name}:")
    for date, temp in top_days:
        print(f"Date: {date}, Temperature: {temp}°F")


def compare_average_temps(dataset_one: HistoricalTemps,
                          dataset_two: HistoricalTemps):
    """
    Compare the average temperatures of two HistoricalTemps datasets.

    Parameters:
        dataset_one (HistoricalTemps): The first temperature dataset.
        dataset_two (HistoricalTemps): The second temperature dataset.
    """
    if not dataset_one.is_data_loaded() or not dataset_two.is_data_loaded():
        print("One or both of the datasets are not loaded.")
        return

    avg_temp_one = dataset_one.average_temp()
    avg_temp_two = dataset_two.average_temp()

    print(f"The average temperature in {dataset_one.loc_name} "
          f"is {avg_temp_one:.2f} degrees.")
    print(f"The average temperature in {dataset_two.loc_name} "
          f"is {avg_temp_two:.2f} degrees.")


def change_dates(dataset: HistoricalTemps):
    """
    Change the start and end dates of the dataset.

    Parameters:
        dataset (HistoricalTemps): The dataset to modify.
    """
    if not dataset.is_data_loaded():
        print("The tempe data is not loaded. Please check dataset.")
        return

    try:
        new_start = input("Enter the new start date (YYYY-MM-DD): ")
        dataset.start = new_start
    except LookupError as e:
        print(f"Failed to change the start date: {e}")
        return

    try:
        new_end = input("Enter the new end date (YYYY-MM-DD): ")
        dataset.end = new_end
    except LookupError as e:
        print(f"Failed to change the end date: {e}")
        return

    print("Dates successfully changed.")


def main():
    """Ask for the user's name, and greet them.

    Then run the function that asks them to choose an option.
    """
    name = input("Please enter your name: ")
    print(f"Hi {name}, let's explore some historical temperatures.")
    print("")
    menu()


def menu():
    """Accept a user's choice from a menu of options.

    Run the function that displays a menu repeatedly until 9 is chosen.
    """
    dataset_one = None
    dataset_two = None
    while True:
        print_menu(dataset_one, dataset_two)
        try:
            option = int(input("What is your choice?"))
        except ValueError:
            print("Please enter a number only")
        else:
            match option:
                case 1:
                    dataset_one = create_dataset()
                case 2:
                    dataset_two = create_dataset()
                case 3:
                    if dataset_one is not None and dataset_two is not None:
                        compare_average_temps(dataset_one, dataset_two)
                    else:
                        print("Both datasets must be loaded before comparing.")
                case 4:
                    if dataset_one is not None:
                        print_extreme_days(dataset_one)
                    else:
                        print("Dataset one must be loaded first.")
                case 5:
                    if dataset_one is not None:
                        print_top_five_days(dataset_one)
                    else:
                        print("Dataset one must be loaded first.")
                case 6:
                    if dataset_one is not None:
                        change_dates(dataset_one)
                    else:
                        print("Dataset one must be loaded first.")
                case 7:
                    if dataset_two is not None:
                        change_dates(dataset_two)
                    else:
                        print("Dataset two must be loaded first.")
                case 9:
                    break
                case _:
                    print("That wasn't a valid selection")
            continue
    print("Goodbye! Thank you for using the database")


def print_menu(dataset_one=None, dataset_two=None):
    """Display a menu of options based on loaded datasets."""
    print("Main Menu")
    if dataset_one is None:
        print("1 - Load dataset one")
    else:
        print(f"1 - Replace {dataset_one.loc_name}")

    if dataset_two is None:
        print("2 - Load dataset two")
    else:
        print(f"2 - Replace {dataset_two.loc_name}")

    print("3 - Compare average temperatures")
    print("4 - Dates above threshold temperature")
    print("5 - Highest historical dates")
    print("6 - Change start and end dates for dataset one")
    print("7 - Change start and end dates for dataset two")
    print("9 - Quit")


if __name__ == "__main__":
    main()

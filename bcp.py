from datetime import datetime
from datetime import timedelta
import os.path
import toml
import sys

class calendar:
    PREFERENCE_SAINTS_DAY_READINGS = True

    CEG_PATH = "./data/collects_epistles_gospels/"
    WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    saints = None
    seasons = {}

    def __init__(self):
        with open(os.path.join(self.CEG_PATH, "saints.toml"), 'r') as fd:
            self.saints = toml.load(fd)
        with open(os.path.join(self.CEG_PATH, "advent.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))
        with open(os.path.join(self.CEG_PATH, "christmastide.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))
        with open(os.path.join(self.CEG_PATH, "epiphany.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))
        with open(os.path.join(self.CEG_PATH, "shrovetide.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))
        with open(os.path.join(self.CEG_PATH, "lent.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))
        with open(os.path.join(self.CEG_PATH, "easter.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))
        with open(os.path.join(self.CEG_PATH, "trinity.toml"), 'r') as fd:
            self.seasons.update(toml.load(fd))


    def _extract_from_day(self, day):
        day_name = day['name']

        try:
            colour = day['colour']
        except KeyError:
            colour = None

        gospel_verse = day['gospel_verse']
        gospel_text = day['gospel_text']
        epistle_verse = day['epistle_verse']
        epistle_text = day['epistle_text']
        
        # There are some Saint's days without collects
        if 'collect' in day.keys():
            collects = day['collect'].split('\n')

        return (day_name, colour, collects, gospel_verse, gospel_text, epistle_verse, epistle_text)


    # Given a int year, calculates Easter Day according to the "Anonymous Gregorian Algorithm"
    def _calculate_easter_day(self, year):
        assert isinstance(year, int)

        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19*a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2*e + 2*i - h - k) % 7
        m = (a + 11*h + 22*l) // 451
        month = (h + l - 7*m + 114) // 31
        day = ((h + l - 7*m + 114) % 31) + 1

        date = datetime(year=year, month=month, day=day)
        return date

    def _calculate_advent_start(self, year):
        st_andrew = datetime(year=year, month=11, day=30)
        if st_andrew.weekday() <= 2:
            advent_offset = (st_andrew.weekday() + 1) * - 1
        else:
            advent_offset = 6 - st_andrew.weekday()
        advent_start = st_andrew + timedelta(days=advent_offset)
        return advent_start


    def _calculate_seasons(self, d):
        assert type(d) is datetime
        # Adjust for liturgical year starting at beginning of advent
        year = d.year
        advent_start = self._calculate_advent_start(year)
        if d < advent_start:
            year = year - 1

        advent_start = self._calculate_advent_start(year)
        next_advent_start = self._calculate_advent_start(year+1)
        christmastide_start = datetime(year=year, month=12, day=25)
        epiphany_start = datetime(year=year+1, month=1, day=6)
        easter_day = self._calculate_easter_day(year+1)
        shrovetide_start = easter_day - timedelta(weeks=9)
        lent_start = easter_day - timedelta(weeks=6)
        eastertide_start = easter_day
        trinity_start = easter_day + timedelta(days=50)

        #print(str((advent_start, christmastide_start, epiphany_start, shrovetide_start, lent_start, eastertide_start, trinity_start, next_advent_start)))
        return(advent_start, christmastide_start, epiphany_start, shrovetide_start, lent_start, eastertide_start, trinity_start, next_advent_start)

        
    def _calculate_week_number(self, season_start, d):
        week_0_days = 7 - ((season_start.weekday() + 1) % 7)
        week_1_start = season_start + timedelta(days=week_0_days)

        if d < week_1_start:
            return 0
        else:
            return ((d - week_1_start).days // 7) + 1


    # Returns the number of standard services in a season
    def _get_standard_services(self, season):
        standard_services = 0
        services = self.seasons[season].keys()
        for service in services:
            try:
                int(service)
                standard_services += 1
            except Exception:
                pass

        return standard_services

    
    # Returns boolean denoting if d is in the final week of the given seasonal period
    def _final_week_of_season(self, season_start, next_season_start, d):
        weeks_in_season = self._calculate_week_number(season_start, next_season_start - timedelta(days=1))
        weeks_of_d = self._calculate_week_number(season_start, d)

        return weeks_in_season == weeks_of_d


    # Returns the day if the day is an exception
    def _extract_from_day_exception(self, season, d):
        (advent_start, christmastide_start, epiphany_start, shrovetide_start, lent_start, eastertide_start, trinity_start, next_advent_start) = self._calculate_seasons(d)

        # Ascension day
        if d == self._calculate_easter_day(d.year) + timedelta(days=39):
            return self.seasons['eastertide']['ascension']

        # Trinity season exceptions
        if season == "trinity":
            # If last week of Trinity, use 26th Sunday of Trinity service
            if self._final_week_of_season(trinity_start, next_advent_start, d):
                return self.seasons['trinity']['last']

            # If running out of Trinity services,
            # Calculates the number of weeks' services need to be moved from the end of Epiphany to the end of Trinity
            # This compensates for extra weeks in Trinity, if Easter is early
            # Edge case on p199 of BCP
            trinity_standard_services = self._get_standard_services('trinity') - 1 # Whitsun week is in eastertide
            weeks_in_trinity = self._calculate_week_number(trinity_start, next_advent_start - timedelta(days=1)) 
            extra_trinity_service_number = self._calculate_week_number(trinity_start, d) - trinity_standard_services

            #print("Trinity standard services: " + str(trinity_standard_services))
            #print("Weeks in trinity: " + str(weeks_in_trinity))
            #print("Extra trinity service number: " + str(extra_trinity_service_number))

            # If we need to insert an additional trinity service
            if extra_trinity_service_number > 0:
                # Start using omitted Epiphany services
                weeks_in_epiphany = self._calculate_week_number(epiphany_start, shrovetide_start - timedelta(days=1))
                week_of_epiphany_service = weeks_in_epiphany + extra_trinity_service_number
                #print("Weeks in epiphany: " + str(weeks_in_epiphany))
                #print("Weeks of epiphany service: " + str(week_of_epiphany_service))
                return self.seasons['epiphany'][str(week_of_epiphany_service)]

        # Not an exception day
        return None


    def _determine_season_colour_ordinary(self, d):
        assert type(d) is datetime

        (advent_start, christmastide_start, epiphany_start, shrovetide_start, lent_start, eastertide_start, trinity_start, next_advent_start) = self._calculate_seasons(d)

        if d >= advent_start and d < christmastide_start:
            return ("advent", "violet", False, self._calculate_week_number(advent_start, d))
        elif d >= christmastide_start and d < epiphany_start:
            return ("christmastide", "white", False, self._calculate_week_number(christmastide_start, d))
        elif d >= epiphany_start and d < shrovetide_start:
            return("epiphany", "green", True, self._calculate_week_number(epiphany_start, d))
        elif d >= shrovetide_start and d < lent_start:
            return("shrovetide", "green", True, self._calculate_week_number(shrovetide_start, d))
        elif d >= lent_start and d < eastertide_start:
            return("lent", "violet", False, self._calculate_week_number(lent_start, d))
        elif d >= eastertide_start and d < trinity_start:
            return("eastertide", "white", False, self._calculate_week_number(eastertide_start, d))
        elif d >= trinity_start and d < next_advent_start:
            return("trinity", "green", True, self._calculate_week_number(trinity_start, d))
        else:
            print("Error in determining liturgical season!")
            sys.exit(1)


    # Returns boolean as to whether a Church service is run this day
    def _is_service_day(self, d):
        if d.weekday() == 6:
            return True
        else:
            return False
        # TODO: encode other non-Sunday service days, e.g. Christmas, etc.

    # Return information about any date in the Anglican year
    def get_date_information(self, d):
        assert type(d) is datetime

        season = None
        ordinary_time = None    # boolean
        saints_day = None       # boolean
        service_name = []
        colour = None
        collects = []
        gospel_verse = None
        gospel_text = None
        epistle_verse = None
        epistle_text = None
        week_number = None

        # Determine season
        (season, colour, ordinary_time, week_number) = self._determine_season_colour_ordinary(d)
        
        # Determine week_day
        week_day = self.WEEKDAY_NAMES[(d.weekday() + 1) % 7]

        # Extract information from BCP about specified Holy day
        date_formatted = str(d.month).zfill(2) + '-' + str(d.day).zfill(2)
        if date_formatted in self.saints['saints'].keys():
            holy_day_info = self.saints['saints'][date_formatted]
            holy_day = True
            (service_name_2, colour_2, collects_2, gospel_verse_2, gospel_text_2, epistle_verse_2, epistle_text_2) = self._extract_from_day(holy_day_info)
        else:
            holy_day_info = None
            holy_day = False

        # Extract information from BCP about specified seasonal day
        #print("season: " + season)
        exceptions_day_info = self._extract_from_day_exception(season, d)
        
        # If d is an exception day, use that. Otherwise use the standard seasonal day
        if exceptions_day_info == None:
            seasons_day_info = self.seasons[season][str(week_number)]
            (service_name_1, colour_1, collects_1, gospel_verse_1, gospel_text_1, epistle_verse_1, epistle_text_1) = self._extract_from_day(seasons_day_info)
        else:
            (service_name_1, colour_1, collects_1, gospel_verse_1, gospel_text_1, epistle_verse_1, epistle_text_1) = self._extract_from_day(exceptions_day_info)

        # Add relevant information to output
        if holy_day:
            if self._is_service_day(d):
                # If Saints day and a service day, add both selectively
                service_name = [service_name_1, service_name_2]
                colour = colour_2
                collects = collects_2 + collects_1
                
                if self.PREFERENCE_SAINTS_DAY_READINGS:
                    gospel_verse = gospel_verse_2
                    gospel_text = gospel_text_2
                    epistle_verse = epistle_verse_2
                    epistle_text = epistle_text_2
                else:
                    gospel_verse = gospel_verse_1
                    gospel_text = gospel_text_1
                    epistle_verse = epistle_verse_1
                    epistle_text = epistle_text_1

            else:
                # If just a Saint's day
                service_name = [service_name_2]
                colour = colour_2
                collects = collects_2
                gospel_verse = gospel_verse_2
                gospel_text = gospel_text_2
                epistle_verse = epistle_verse_2
                epistle_text = epistle_text_2
        else:
            # If not a Saint's day
            service_name = [service_name_1]
            collects = collects_1
            gospel_verse = gospel_verse_1
            gospel_text = gospel_text_1
            epistle_verse = epistle_verse_1
            epistle_text = epistle_text_1

        # TODO: Add required seasonal collects
        # TODO: Rename Saint's day, Holy Day
        # TODO: Add extra feasts as shown in BCP table, page lv
        
        info = {
            "week_day": week_day,
            "season": season,
            "colour": colour,
            "week_number": week_number,
            "ordinary_time": ordinary_time,
            "holy_day": holy_day,
            "service_name": service_name,
            "collects": collects,
            "epistle_verse": epistle_verse,
            "epistle_text": epistle_text,
            "gospel_verse": gospel_verse,
            "gospel_text": gospel_text
        }

        return info



from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import List, Optional



class SportType(Enum):
    PADEL = "padel"
    FOOTBALL = "football"


class FootballPosition(Enum):
    GOALKEEPER = "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"


class PadelPosition(Enum):
    LEFT = "left"
    RIGHT = "right"
    NO_PREFERENCE = "no_preference" 


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"



@dataclass
class TimeSlot:
    day: int          
    start_time: time
    end_time: time



@dataclass
class PlayerSportProfile:
    sport: SportType                                   
    skill_level: float                                  

    preferred_position: Optional[FootballPosition | PadelPosition] = None
    number_of_matches: int = 0                         
    rating: float = 3.0                                  



@dataclass
class Player:
    id: int
    name: str


    age: Optional[int] = None
    gender: Optional[Gender] = None


    preferred_latitude: Optional[float] = None
    preferred_longitude: Optional[float] = None


    preferred_times: List[TimeSlot] = field(default_factory=list)

    sport_profiles: List[PlayerSportProfile] = field(default_factory=list)

    def get_profile(self, sport: SportType) -> Optional[PlayerSportProfile]:
        return next((p for p in self.sport_profiles if p.sport == sport), None)



@dataclass
class MatchRequest:
    sport: SportType
    required_players: int                   
    latitude: float
    longitude: float
    match_datetime: datetime
    required_positions: List[FootballPosition | PadelPosition] = field(default_factory=list)

    required_gender: Optional[Gender] = None



class MatchmakingService:
   
    W_SKILL = 0.35        
    W_LOCATION = 0.25      
    W_RATING = 0.20        
    W_TIME = 0.10          
    W_EXPERIENCE = 0.10    

    MAX_DISTANCE_KM = 30.0    
    SOFT_RANGE_KM = 100.0     
                               
    MAX_SKILL_DIFF = 6.0   
    def calculate_compatibility_score(self, player: Player, request: MatchRequest) -> float:

        profile = player.get_profile(request.sport)
        if profile is None:
            return 0.0

        if request.required_positions and not self._position_eligible(profile, request):
            return 0.0

        if request.required_gender is not None and player.gender != request.required_gender:
            return 0.0

        skill_score = self._score_skill(profile.skill_level)
        location_score = self._score_location(player, request)  
        rating_score = profile.rating / 5.0  
        time_score = self._score_time(player, request)  
        experience_score = self._score_experience(profile.number_of_matches)

        total = (
            self.W_SKILL * skill_score
            + self.W_LOCATION * location_score
            + self.W_RATING * rating_score
            + self.W_TIME * time_score
            + self.W_EXPERIENCE * experience_score
        )

        return max(0.0, min(1.0, total))


    def _position_eligible(self, profile: PlayerSportProfile, request: MatchRequest) -> bool:

        player_position = profile.preferred_position

        if profile.sport == SportType.PADEL and player_position == PadelPosition.NO_PREFERENCE:
            return True  # مرن، يتقبله أي فريق محتاج يمين أو شمال

        if player_position is None:
            return False

        return player_position in request.required_positions

    def _score_skill(self, player_skill: float) -> float:

        diff = abs(player_skill - 4.0)  
        return 1 - (diff / self.MAX_SKILL_DIFF)

    def _score_location(self, player: Player, request: MatchRequest) -> float:
       
        if player.preferred_latitude is None or player.preferred_longitude is None:
            return 0.0  

        distance = self._haversine_distance_km(
            player.preferred_latitude, player.preferred_longitude,
            request.latitude, request.longitude,
        )

        if distance <= self.MAX_DISTANCE_KM:
           
            return 1 - (distance / self.MAX_DISTANCE_KM)

        return max(0.0, 1 - (distance / self.SOFT_RANGE_KM))

    def _score_time(self, player: Player, request: MatchRequest) -> float:
        if not player.preferred_times:
            return 1.0  

        day = request.match_datetime.weekday()
        match_time = request.match_datetime.time()

        matches = any(
            slot.day == day and slot.start_time <= match_time <= slot.end_time
            for slot in player.preferred_times
        )

        return 1.0 if matches else 0.2

    def _score_experience(self, number_of_matches: int) -> float:
  
        return min(number_of_matches / 20.0, 1.0)

    def rank_candidates(
        self, candidates: List[Player], request: MatchRequest
    ) -> List[tuple[Player, float]]:

        scored = [
            (player, self.calculate_compatibility_score(player, request))
            for player in candidates
        ]
        eligible = [(p, s) for p, s in scored if s > 0]
        eligible.sort(key=lambda x: x[1], reverse=True)
        return eligible

    @staticmethod
    def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371  # نصف قطر الأرض بالكيلومتر
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c


import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.tools.planner_tools import PlannerTools


class PlannerAgent:
    def __init__(self):
        """
        여행 계획 생성을 담당하는 에이전트
        """
        self.logger = logging.getLogger(__name__)
        self.planner_tools = PlannerTools()

    def generate_initial_plan(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        검색 결과를 바탕으로 초기 여행 계획 생성

        Args:
            search_results (Dict[str, Any]): 검색 에이전트로부터 받은 검색 결과

        Returns:
            Dict[str, Any]: 초기 여행 계획
        """
        self.logger.info("초기 여행 계획 생성 시작")

        # 여행 기본 정보 추출
        destinations = search_results.get(
            'travel_details', {}).get('destinations', [])
        attractions = search_results.get(
            'travel_details', {}).get('attractions', [])

        # 여행 기간 및 일정 생성
        trip_duration = self._calculate_trip_duration(destinations)
        daily_itinerary = self._create_daily_itinerary(
            destinations, attractions, trip_duration)

        initial_plan = {
            'destinations': destinations,
            'trip_duration': trip_duration,
            'daily_itinerary': daily_itinerary,
            'transportation': self._recommend_transportation(destinations),
            'accommodation': self._recommend_accommodation(destinations),
            'budget_estimate': self._estimate_budget(destinations, trip_duration)
        }

        self.logger.info("초기 여행 계획 생성 완료")
        return initial_plan

    def _calculate_trip_duration(self, destinations: List[str]) -> Dict[str, Any]:
        """
        목적지 수와 특성에 따라 여행 기간 계산

        Args:
            destinations (List[str]): 여행 목적지 목록

        Returns:
            Dict[str, Any]: 여행 기간 정보
        """
        base_days = 3  # 기본 여행 기간
        additional_days_per_destination = 2  # 추가 목적지당 일수

        total_duration = base_days + \
            (len(destinations) - 1) * additional_days_per_destination

        return {
            'total_days': total_duration,
            'start_date': datetime.now() + timedelta(days=30),  # 한 달 후 여행 가정
            'end_date': datetime.now() + timedelta(days=30 + total_duration)
        }

    def _create_daily_itinerary(self, destinations: List[str], attractions: List[str], trip_duration: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        목적지와 관광지를 고려한 일일 일정 생성

        Args:
            destinations (List[str]): 여행 목적지
            attractions (List[str]): 관광지 목록
            trip_duration (Dict[str, Any]): 여행 기간 정보

        Returns:
            List[Dict[str, Any]]: 일일 일정
        """
        daily_itinerary = []
        current_date = trip_duration['start_date']

        for day in range(1, trip_duration['total_days'] + 1):
            day_plan = {
                'day': day,
                'date': current_date.strftime('%Y-%m-%d'),
                'destination': destinations[day % len(destinations)],
                'activities': self._select_daily_activities(attractions),
                'meals': self._recommend_meals()
            }

            daily_itinerary.append(day_plan)
            current_date += timedelta(days=1)

        return daily_itinerary

    def _select_daily_activities(self, attractions: List[str], max_activities: int = 3) -> List[str]:
        """
        관광지 중 일일 활동 선택

        Args:
            attractions (List[str]): 관광지 목록
            max_activities (int): 하루 최대 활동 수

        Returns:
            List[str]: 선택된 활동 목록
        """
        return attractions[:max_activities]

    def _recommend_transportation(self, destinations: List[str]) -> Dict[str, Any]:
        """
        목적지 간 이동 교통수단 추천

        Args:
            destinations (List[str]): 여행 목적지

        Returns:
            Dict[str, Any]: 교통수단 추천 정보
        """
        return {
            'between_cities': '기차' if len(destinations) > 1 else '해당 없음',
            'local_transportation': '대중교통 추천'
        }

    def _recommend_accommodation(self, destinations: List[str]) -> List[Dict[str, Any]]:
        """
        목적지별 숙박 시설 추천

        Args:
            destinations (List[str]): 여행 목적지

        Returns:
            List[Dict[str, Any]]: 숙박 시설 추천 목록
        """
        return [{'destination': dest, 'type': '호텔 또는 게스트하우스'} for dest in destinations]

    def _estimate_budget(self, destinations: List[str], trip_duration: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 예산 추정

        Args:
            destinations (List[str]): 여행 목적지
            trip_duration (Dict[str, Any]): 여행 기간 정보

        Returns:
            Dict[str, Any]: 예산 추정 정보
        """
        daily_budget = 100000  # 1인당 하루 평균 예산 (원)
        total_budget = daily_budget * \
            trip_duration['total_days'] * len(destinations)

        return {
            'daily_budget': daily_budget,
            'total_budget': total_budget,
            'budget_per_destination': total_budget / len(destinations)
        }

    def execute(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        플래너 에이전트의 주요 실행 메서드

        Args:
            search_results (Dict[str, Any]): 검색 에이전트로부터 받은 검색 결과

        Returns:
            Dict[str, Any]: 생성된 여행 계획
        """
        initial_plan = self.generate_initial_plan(search_results)
        return initial_plan




import logging
from typing import Any, Dict, List

from src.tools.verifier_tools import VerifierTools


class VerifierAgent:
    def __init__(self):
        """
        여행 계획 검증을 담당하는 에이전트
        """
        self.logger = logging.getLogger(__name__)
        self.verifier_tools = VerifierTools()

    def verify_plan(self, initial_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        초기 여행 계획 검증 및 개선

        Args:
            initial_plan (Dict[str, Any]): 초기 여행 계획

        Returns:
            Dict[str, Any]: 검증 및 개선된 여행 계획
        """
        self.logger.info("여행 계획 검증 시작")

        verified_plan = initial_plan.copy()

        # 계획 검증 단계
        verified_plan['feasibility_check'] = self._check_plan_feasibility(
            initial_plan)
        verified_plan['budget_optimization'] = self._optimize_budget(
            initial_plan)
        verified_plan['safety_assessment'] = self._assess_safety(initial_plan)
        verified_plan['weather_compatibility'] = self._check_weather_compatibility(
            initial_plan)

        # 개선 사항 적용
        if not verified_plan['feasibility_check']['is_feasible']:
            verified_plan = self._adjust_plan_for_feasibility(verified_plan)

        self.logger.info("여행 계획 검증 완료")
        return verified_plan

    def _check_plan_feasibility(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 계획의 실현 가능성 검토

        Args:
            plan (Dict[str, Any]): 검증할 여행 계획

        Returns:
            Dict[str, Any]: 실현 가능성 검토 결과
        """
        feasibility_checks = {
            'destinations_reachable': True,
            'activities_realistic': True,
            'time_management': True,
            'is_feasible': True
        }

        # 목적지 간 이동 시간 및 거리 검토
        destinations = plan.get('destinations', [])
        if len(destinations) > 1:
            feasibility_checks['destinations_reachable'] = self.verifier_tools.check_destination_connectivity(
                destinations)

        # 일정별 활동 현실성 검토
        daily_itinerary = plan.get('daily_itinerary', [])
        feasibility_checks['activities_realistic'] = self.verifier_tools.validate_daily_activities(
            daily_itinerary)

        # 시간 관리 검토
        feasibility_checks['time_management'] = self.verifier_tools.check_time_allocation(
            daily_itinerary)

        feasibility_checks['is_feasible'] = all(feasibility_checks.values())

        return feasibility_checks

    def _optimize_budget(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 예산 최적화

        Args:
            plan (Dict[str, Any]): 원본 여행 계획

        Returns:
            Dict[str, Any]: 예산 최적화 제안
        """
        budget_estimate = plan.get('budget_estimate', {})
        total_budget = budget_estimate.get('total_budget', 0)

        optimization_suggestions = {
            'current_budget': total_budget,
            'potential_savings': 0,
            'recommended_adjustments': []
        }

        # 숙박비 절감 방안
        accommodation_savings = self.verifier_tools.find_budget_accommodation(
            plan.get('destinations', []))
        if accommodation_savings:
            optimization_suggestions['recommended_adjustments'].append({
                'category': '숙박',
                'suggestion': accommodation_savings
            })
            optimization_suggestions['potential_savings'] += accommodation_savings.get(
                'savings', 0)

        # 식비 절감 방안
        meal_savings = self.verifier_tools.find_budget_meal_options(
            plan.get('destinations', []))
        if meal_savings:
            optimization_suggestions['recommended_adjustments'].append({
                'category': '식비',
                'suggestion': meal_savings
            })
            optimization_suggestions['potential_savings'] += meal_savings.get(
                'savings', 0)

        return optimization_suggestions

    def _assess_safety(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 안전성 평가

        Args:
            plan (Dict[str, Any]): 여행 계획

        Returns:
            Dict[str, Any]: 안전성 평가 결과
        """
        destinations = plan.get('destinations', [])
        safety_assessment = {
            'overall_safety_level': '보통',
            'safety_warnings': [],
            'recommended_precautions': []
        }

        for destination in destinations:
            destination_safety = self.verifier_tools.check_destination_safety(
                destination)
            safety_assessment['safety_warnings'].extend(
                destination_safety.get('warnings', []))
            safety_assessment['recommended_precautions'].extend(
                destination_safety.get('precautions', []))

        # 안전 수준 종합 평가
        if safety_assessment['safety_warnings']:
            safety_assessment['overall_safety_level'] = '주의'

        return safety_assessment

    def _check_weather_compatibility(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        여행 계획과 날씨 호환성 검토

        Args:
            plan (Dict[str, Any]): 여행 계획

        Returns:
            Dict[str, Any]: 날씨 호환성 검토 결과
        """
        trip_duration = plan.get('trip_duration', {})
        destinations = plan.get('destinations', [])

        weather_compatibility = {
            'destinations_weather': {},
            'overall_compatibility': '적합',
            'recommended_adjustments': []
        }

        for destination in destinations:
            destination_weather = self.verifier_tools.check_destination_weather(
                destination,
                trip_duration.get('start_date'),
                trip_duration.get('end_date')
            )
            weather_compatibility['destinations_weather'][destination] = destination_weather

            if destination_weather.get('recommendation') != '적합':
                weather_compatibility['overall_compatibility'] = '부분 부적합'
                weather_compatibility['recommended_adjustments'].append({
                    'destination': destination,
                    'suggestion': destination_weather.get('suggestion')
                })

        return weather_compatibility

    def _adjust_plan_for_feasibility(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        실현 불가능한 계획 조정

        Args:
            plan (Dict[str, Any]): 조정이 필요한 여행 계획

        Returns:
            Dict[str, Any]: 조정된 여행 계획
        """
        adjusted_plan = plan.copy()

        # 목적지 간 이동성 개선
        if not plan['feasibility_check']['destinations_reachable']:
            adjusted_plan['destinations'] = self.verifier_tools.optimize_destination_route(
                plan['destinations'])

        # 일정 현실성 개선
        if not plan['feasibility_check']['activities_realistic']:
            adjusted_plan['daily_itinerary'] = self.verifier_tools.adjust_daily_activities(
                plan['daily_itinerary'])

        # 시간 관리 개선
        if not plan['feasibility_check']['time_management']:
            adjusted_plan['daily_itinerary'] = self.verifier_tools.optimize_time_allocation(
                plan['daily_itinerary'])

        return adjusted_plan

    def execute(self, initial_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        검증 에이전트의 주요 실행 메서드

        Args:
            initial_plan (Dict[str, Any]): 초기 여행 계획

        Returns:
            Dict[str, Any]: 검증 및 개선된 여행 계획
        """
        verified_plan = self.verify_plan(initial_plan)
        return verified_plan




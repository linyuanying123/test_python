from typing import List, Optional

class BinarySearch:
    """
    二分查找算法工具类
    提供多种二分查找算法的实现
    """
    
    @staticmethod
    def search(sorted_list: List[int], target: int) -> Optional[int]:
        """
        标准二分查找实现
        :param sorted_list: 已排序的列表(升序)
        :param target: 要查找的目标值
        :return: 目标值索引，未找到返回None
        """
        left, right = 0, len(sorted_list) - 1
        
        while left <= right:
            mid = left + (right - left) // 2
            if sorted_list[mid] == target:
                return mid
            elif sorted_list[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return None

    @staticmethod
    def find_first(sorted_list: List[int], target: int) -> Optional[int]:
        """
        查找第一个等于目标值的位置
        :param sorted_list: 已排序的列表(升序)
        :param target: 要查找的目标值
        :return: 第一个匹配的索引，未找到返回None
        """
        left, right = 0, len(sorted_list) - 1
        result = None
        
        while left <= right:
            mid = left + (right - left) // 2
            if sorted_list[mid] >= target:
                right = mid - 1
                if sorted_list[mid] == target:
                    result = mid
            else:
                left = mid + 1
        return result

    @staticmethod
    def find_last(sorted_list: List[int], target: int) -> Optional[int]:
        """
        查找最后一个等于目标值的位置
        :param sorted_list: 已排序的列表(升序)
        :param target: 要查找的目标值
        :return: 最后一个匹配的索引，未找到返回None
        """
        left, right = 0, len(sorted_list) - 1
        result = None
        
        while left <= right:
            mid = left + (right - left) // 2
            if sorted_list[mid] <= target:
                left = mid + 1
                if sorted_list[mid] == target:
                    result = mid
            else:
                right = mid - 1
        return result

    @staticmethod
    def find_closest(sorted_list: List[int], target: int) -> int:
        """
        查找最接近目标值的位置
        :param sorted_list: 已排序的列表(升序)
        :param target: 要查找的目标值
        :return: 最接近值的索引
        """
        left, right = 0, len(sorted_list) - 1
        
        while left < right - 1:
            mid = left + (right - left) // 2
            if sorted_list[mid] < target:
                left = mid
            else:
                right = mid
                
        if abs(sorted_list[left] - target) <= abs(sorted_list[right] - target):
            return left
        return right

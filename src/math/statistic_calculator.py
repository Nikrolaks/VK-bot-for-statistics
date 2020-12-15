# -*- coding: UTF-8 -*-
class ContentTimeComputer:

    number_of_timepoints = 47
    expectation_mat_change_coefficient = 100

    number_of_online = []
    income_online = []

    def __init__(self):
        for i in range(self.number_of_timepoints):
            self.number_of_online.append(0)
            self.income_online.append(0)

    def counting_new_online(self, user_list1, user_list2):
        """
        работает за O(m+n)
        где m, n - количества пользователей
        :param user_list1: массивы, содержащие айдишники пользователей (только числа, понятно)
        :param user_list2:
        :return: возвращаем число присоединившихся
        """
        count = 0
        i = 0
        j = 0
        while i < len(user_list1):
            while j < len(user_list2):
                if user_list2[j] == user_list1[i]:
                    count += 1
                    j += 1
                    break
                elif user_list2[j] > user_list1[i]:
                    break
                j += 1
            i += 1
        return len(user_list2) - count

    def correct_number_of_online(self, time, number_of_online_now):
        """
        корректируем матожидание количества пользователей онлайн
        :param time: время корректировки - целое число, интервал разбиения суток на такие периоды задаем константой
        """
        self.number_of_online[time] = (number_of_online_now + self.number_of_online[time]) / self.expectation_mat_change_coefficient

    def correct_income_online(self, time, user_list1, user_list2):
        """
        корректируем матожидание количества пользователей зашедших в онлайн за последние 30 минут
        :param user_list1: (см. описание соответствующей функции)
        :param user_list2:
        :param time: (см. ранее)
        """
        self.income_online[time] = (self.counting_new_online(user_list1, user_list2) + self.number_of_online[time]) / self.expectation_mat_change_coefficient

    def calculate_effective_time(self):
        """
        :return: возвращаем время в которое пост наберет наибольшее количество просмотров
        """
        time_max = 0
        for i in range(self.number_of_timepoints):
            if self.number_of_online[i]+self.income_online[(i+1)%self.number_of_timepoints] > \
               self.number_of_online[time_max]+self.income_online[(time_max+1)%self.number_of_timepoints]:
                time_max = i
        return time_max
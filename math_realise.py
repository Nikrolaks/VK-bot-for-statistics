# -*- coding: UTF-8 -*-
import time
import numpy as np
import matplotlib.pyplot as plt


class ContentTimeComputer:

    """
    int:param number_of_time_intervals : константа, указывающая сколько временных промежутков мы смотрим (сейчас 7 дней,
     каждый час, т.е. мы 7 дней делим на столько тиков), в программе работает на тиках
    int:param expectation_math_change_coefficient: коэффициент, указывающий насколько мало изменится матожидание от
     одного
    замера (меняется с течением времени от 1 до const_expectation_math_change_coefficient
    int:param const_expectation_math_change_coefficient: максимальное значение expectation_math_change_coefficient,
    !!!ВАЖНО!!! инициализируется пользователем в конструкторе
    int:param counter_of_expectation_math_change_coefficient_change: счетчик количества замеров (нужен для ускорения
     построения модели)
    это все были переменные типа int
    float[]:param expectation_of_users_online[]: массив, в котором содержится матожидание количества человек онлайн
    в определенный момент времени
    float[]:param expectation_of_income_online[]: массив, в котором содержится матожидание количества человек, зашедших
    в онлайн между 2 замерами в определенный момент времени
    int:param monitoring_start_time: время начала работы программы для определенного паблика (дается во входных данных в
     количестве секунд с 1.01.1970, но в программе преобразуется в тики)(используется ТОЛЬКО для инициализации time
      и НЕ ХРАНИТСЯ)
    int:param time: время (в тиках, с начала текущей недели)
    """
    time = 0
    number_of_time_intervals = 0
    expectation_math_change_coefficient = 0
    const_expectation_math_change_coefficient = 0
    expectation_of_users_online = []
    expectation_of_income_online = []
    counter_of_expectation_math_change_coefficient_change = 0

    def __init__(self, const_expectation_math_change_coefficient_input, number_of_time_intervals_input,
                 monitoring_start_time):
        self.const_expectation_math_change_coefficient = const_expectation_math_change_coefficient_input
        self.number_of_time_intervals = number_of_time_intervals_input
        self.time = (monitoring_start_time // (604800 // number_of_time_intervals_input))%number_of_time_intervals_input
        # преобразуем время в количество тиков,
        # в неделе 604800 секунд
        for i in range(self.number_of_time_intervals):
            self.expectation_of_users_online.append(0.0)
            self.expectation_of_income_online.append(0.0)

    def counting_new_online(self, user_list_were, user_list_now):
        """
        работает за O(m+n)
        где m, n - количества пользователей
        int[]:param user_list_were: массив, содержащие айдишники пользователей которые были в предыдущем просмотре [int]
        int[]:param user_list_now: массив, содержащие айдишники пользователей в текущем просмотре [int]
        int:return: возвращаем число присоединившихся int
        """
        count = 0
        i = 0
        j = 0
        while i < len(user_list_were):
            while j < len(user_list_now):
                if user_list_now[j] == user_list_were[i]:
                    count += 1
                    j += 1
                    break
                elif user_list_now[j] > user_list_were[i]:
                    break
                j += 1
            i += 1
        return len(user_list_now) - count

    def correct_number_of_online(self, number_of_online_now):
        """
        корректируем матожидание количества пользователей онлайн
        int:param number_of_online_now: количество пользователей онлайн в данный момент времени
        """

        self.correct_expectation_math_change_coefficient()
        self.time = (self.time + 1) % self.number_of_time_intervals
        self.expectation_of_users_online[self.time] = \
            number_of_online_now * \
            (1 - 1 / self.expectation_math_change_coefficient) + \
            (self.expectation_of_users_online[self.time]) / \
            self.expectation_math_change_coefficient

    def correct_income_online(self, user_list_were, user_list_now):
        """
        корректируем матожидание количества пользователей зашедших в онлайн
        int[]:param user_list_were: (см. описание соответствующей функции)
        int[]:param user_list_now:
        """
        self.correct_expectation_math_change_coefficient()
        self.expectation_of_income_online[self.time] = \
            self.counting_new_online(user_list_were, user_list_now) * (
                    1 - 1 / self.expectation_math_change_coefficient) + \
            (self.expectation_of_users_online[self.time]) / self.expectation_math_change_coefficient

    def calculate_effective_time(self):
        """
        class time:return: возвращаем время в которое пост наберет наибольшее количество просмотров str
        """
        time_max = 0
        for i in range(self.number_of_time_intervals):
            if self.expectation_of_users_online[i] + self.expectation_of_income_online[
                (i + 1) % self.number_of_time_intervals] > \
                    self.expectation_of_users_online[time_max] + \
                    self.expectation_of_income_online[(time_max + 1) % self.number_of_time_intervals]:
                time_max = i
        time_max = time_max * 604800 // self.number_of_time_intervals
        seconds_from_begin_1970 = time.time()
        seconds_from_begin_1970 = seconds_from_begin_1970 - (seconds_from_begin_1970 % 604800) + 334800
        return time.ctime(time_max + seconds_from_begin_1970)

    def correct_expectation_math_change_coefficient(self):
        """
        корректируем коэффициент изменения матожидания (иначе статистика будет собираться млрд лет)
        """
        if self.counter_of_expectation_math_change_coefficient_change % self.number_of_time_intervals == 0 and \
                self.const_expectation_math_change_coefficient > self.expectation_math_change_coefficient:
            self.expectation_math_change_coefficient += 1
        self.counter_of_expectation_math_change_coefficient_change += 1

    def draw_diagram(self, save_file):
        """
        str:param save_file название файла в который сохраняем изображение диаграммы
        рисуем диаграмму и сохраняем в save_file
        """
        dpi = 80
        fig = plt.figure(dpi=dpi, figsize=(512 / dpi, 384 / dpi))
        max_val = 0
        xtickets = fig.add_subplot(212)

        for i in range(self.number_of_time_intervals):
            if abs(max_val) < abs(self.expectation_of_users_online[i]):
                max_val = abs(self.expectation_of_users_online[i])
            if abs(max_val) < abs(self.expectation_of_income_online[i]):
                max_val = abs(self.expectation_of_income_online[i])

        plt.axis([0, self.number_of_time_intervals, -max_val, max_val])
        plt.title("Активность пользователей", fontsize=20)
        labels = ['Mon', 'Tue', 'Wed', 'The','Fri','Sat','Sun']
        plt.bar([x for x in range(self.number_of_time_intervals)], self.expectation_of_users_online, width=0.3,
                color='b')
        plt.bar([x+0.3 for x in range(self.number_of_time_intervals)], self.expectation_of_income_online, width=0.3,
                color='r')
        xtickets.set_xticklabels(labels, color='black', rotation=315)
        plt.show()

        fig.savefig(save_file)


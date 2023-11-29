import random
from tabulate import tabulate

N_DAYS = 5
CLASSES_PER_DAY = 5
GROUPS = ['TK-41', 'TK-42', 'TTP-41', 'TTP-42', 'MI-41', 'MI-42']
SUBJECTS = ['IS', 'Quants', 'Refactoring', 'SPP', 'Image recognition', 'Management']
TEACHERS = ['Kulyabko', 'Derevyanchenko', 'Glibovec', 'Vergunova', 'Bobil', 'Ryabokon']
ROOMS = ['101', '202', '303', '404', '505']


class CspScheduler:
    def __init__(self, rooms, groups, subjects, teachers, n_days, n_lessons):
        self.rooms = rooms
        self.groups = groups
        self.subjects = subjects
        self.teachers = teachers
        self.n_days = n_days
        self.n_lessons = n_lessons
        self.total_lessons = n_days * n_lessons

        subjects_per_teacher = 4
        subjects_per_group = 3

        self.teacher_skills = []
        for ti in range(len(self.teachers)):
            self.teacher_skills.append(set())
            for si in range(subjects_per_teacher):
                # Semi-random distribution
                self.teacher_skills[ti].add((si ** 2 + ti ** 2) % len(self.subjects))

        # The subjects to be taught to each group
        self.subs_for_groups = []
        for gi in range(len(self.groups)):
            self.subs_for_groups.append(set())
            for si in range(subjects_per_group):
                self.subs_for_groups[gi].add((si ** 2 + gi) % len(self.subjects))

        # room per lesson per group
        self.rpl = [[] * len(self.groups) for _ in range(self.total_lessons)]

        # subject per lesson per group
        self.spl = [[] * len(self.groups) for _ in range(self.total_lessons)]

        # teacher per lesson per group
        self.tpl = [[] * len(self.groups) for _ in range(self.total_lessons)]

        self.cnt = 0

    def is_complete(self):
        for l in self.rpl:
            if any(r is None for r in l):
                return False
        return True

    def check_constraints(self):
        self.cnt += 1

        if self.cnt > 1e6:
            return False

        # Constraint 1: Check if each class has both labs and lectures
        if self.is_complete():
            for group in range(len(self.groups)):
                classes_per_subjects = {subject: set() for subject in self.subs_for_groups[group]}
                if any([len(classes) != 2 for classes in classes_per_subjects.values()]):
                    return False

        # Constraint 2: Check if each teacher can teach only 1 group at a time
        for teacher_group in self.tpl:
            for i in range(len(self.groups) - 1):
                if teacher_group[i] is not None and teacher_group[i] in teacher_group[i + 1:]:
                    return False

        # Constraint 3: Check if each room can be used only by 1 group at a time
        for room_group in self.rpl:
            for i in range(len(self.groups) - 1):
                if room_group[i] is not None and room_group[i] in room_group[i + 1:]:
                    return False

        # Constraints 4 and 5 are already specified in the backtracking method

        # Constraint 6: Check if each group can only visit 1 class at a time
        # This constraint is already maintained by the code structure

        return True

    def setter(self, lesson, group, teacher, room, subject):
        self.tpl[lesson][group] = teacher
        self.rpl[lesson][group] = room
        self.spl[lesson][group] = subject

    def select_unassigned_var(self):
        for lesson in range(self.total_lessons):
            for group in range(len(self.groups)):
                if self.tpl[lesson][group] is None:
                    return lesson, group

    def degree_heuristic(self):
        none_count = []
        for lesson in range(self.total_lessons):
            count = sum([self.tpl[lesson][group] is None for group in range(len(self.groups))])
            none_count.append(count)
        lesson_index = none_count.index(max(none_count))
        for group in range(len(self.groups)):
            if self.tpl[lesson_index][group] is None:
                return lesson_index, group

    def mrv(self):
        for day in range(self.n_days):
            for lesson in range(self.n_lessons):
                lesson_index = day * self.n_lessons + lesson
                for group in range(len(self.groups)):
                    if self.tpl[lesson_index][group] is None:
                        return lesson_index, group

    def order_domain_vals(self, group):
        for teacher in random.sample(range(len(self.teachers)), len(self.teachers)):
            available_subjects = list(self.subs_for_groups[group].intersection(self.teacher_skills[teacher]))
            for room in random.sample(range(len(self.rooms)), len(self.rooms)):
                for subject in random.sample(available_subjects, len(available_subjects)):
                    yield teacher, room, subject

    def lcv(self, group):
        teacher_scores = []
        for teacher in range(len(self.teachers)):
            score = 0
            for other_group in range(len(self.groups)):
                if other_group != group:
                    score += len(self.teacher_skills[teacher].intersection(self.subs_for_groups[other_group]))
            teacher_scores.append([score, teacher])
        for _, teacher in sorted(teacher_scores):
            available_subjects = list(self.subs_for_groups[group].intersection(self.teacher_skills[teacher]))
            for room in random.sample(range(len(self.rooms)), len(self.rooms)):
                for subject in random.sample(available_subjects, len(available_subjects)):
                    yield teacher, room, subject

    def forward_check(self, lesson, group):
        for teacher in random.sample(range(len(self.teachers)), len(self.teachers)):
            if teacher not in self.tpl[lesson]:
                available_subjects = list(self.subs_for_groups[group].intersection(self.teacher_skills[teacher]))
                for room in random.sample(range(len(self.rooms)), len(self.rooms)):
                    if room not in self.rpl[lesson]:
                        for subject in random.sample(available_subjects, len(available_subjects)):
                            yield teacher, room, subject

    def backtracking(self):
        unassigned_var = self.select_unassigned_var()
        if unassigned_var is None:
            return True

        lesson, group = unassigned_var

        for teacher, room, subject in self.order_domain_vals(
                group):  # self.forward_check(lesson, group): # self.lcv(group):
            self.setter(lesson, group, teacher, room, subject)
            if self.check_constraints():
                result = self.backtracking()
                if result:
                    return True
            self.setter(lesson, group, None, None, None)
        return False

    def print_timetable(self):
        table = {"indices": ["Day", "Group"]}
        for day in range(self.n_days):
            for group in range(1, len(self.groups)):
                table[(day, group)] = [""]
            for group in range(len(self.groups)):
                table[(day, group)].append(GROUPS[group])
                for lesson in range(self.n_lessons):
                    lesson_index = day * self.n_lessons + lesson
                    lesson_desc = (f"{self.subjects[self.spl[lesson_index][group]]}\n"
                                   f"Room: {self.rooms[self.rpl[lesson_index][group]]}\n"
                                   f"Prof.: {self.teachers[self.tpl[lesson_index][group]]}")
                    table[(day, group)].append(lesson_desc)
            table[(day, -1)] = [""] * (2 + self.n_lessons)
        print(tabulate(table, tablefmt="fancy_grid"))


if __name__ == '__main__':
    csp = CspScheduler(ROOMS, GROUPS, SUBJECTS, TEACHERS, N_DAYS, CLASSES_PER_DAY)
    csp.backtracking()
    csp.print_timetable()

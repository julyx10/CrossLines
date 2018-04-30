# -*- coding:utf-8 -*-
from __future__ import unicode_literals

'''
    Coding by liulichuan@live.cn
    Date: 2018-4-1
'''

import pygame
from pygame.locals import *
import sys
import time
import math
import random

# const value
consts = {
    "screen_size": (800, 600),
    "margin": 16,                # space between the main window and the play area
    "vertex_size": 18,           # diameter of the vertex circus
    "fps": 30,                   # frames per second
}

colors = {
    "background": (43, 43, 43),     # pycharm's background color
    "text": (128, 128, 128),        # text color
    "line": (66, 133, 244),         # google blue
    "crossed_line": (234, 67, 53),  # google red
}

# localization strings
langs = {
    "caption": "Crossed Lines",
    "crossed_lines": "crossed lines",
    "time_elapsed": "s",
}

# bitmap resources
resources = {
    "wallpaper":    'Res\\wallpaper_800x600.png',
    "ball_r":       'Res\\google_red_32.png',
    "ball_g":       'Res\\google_green_32.png',
    "ball_y":       'Res\\google_yellow_32.png',
    "ball_b":       'Res\\google_blue_32.png',
}


class GameInfo:
    def __init__(self, game_rect):
        # game init
        self.rect = game_rect   # rect of game area

        # new game
        self.num_of_vertexes = 0
        self.level = 0          # index of new game level
        self.bk_color = 0       # background color of new game
        self.start_time = None  # time when new game started
        self.finished_time = None   # time elapsed when game finished
        self.finished = False     # True when game passed
        self.auto_move = False    # if transformed, set True
        self.show_end_pos = True  # True, transform from play_pos to end_pos, vice versa

        self.vertexes = []      # list of vertexes (class)
        self.lines = []         # list of lines

        self.num_of_all_lines = 0   # count of all lines
        self.num_of_crossed_lines = 0    # count of all crossed lines when beginning new game
        self.num_of_crossed_lines_left = 0    # count of all crossed lines left
        self.selected_id = -1     # current id of selected vertex

    def new_level(self, num_of_vertexes):
        '''
        new game level
        :param num_of_vertexes: number of all vertexes
        :return:
        '''
        self.num_of_vertexes = num_of_vertexes
        self.level += 1         # new game level id
        self.bk_color = (random.randrange(0, 50, 5), random.randrange(0, 50, 5), random.randrange(0, 50, 5))
        self.start_time = time.time()
        self.finished_time = self.start_time
        self.finished = False
        self.auto_move = False
        self.show_end_pos = True

        self.vertexes = []
        # 1. generate random position of all vertex
        for i in range(self.num_of_vertexes):
            vertex = Vertex(self.rect, i, self.num_of_vertexes)
            vertex.generate()
            self.vertexes.append(vertex)

        # 2. create no crossed lines among all vertex
        self.create_no_crossed_lines()   # set value of self.lines[]

        # 3. shuffle the vertexes to a circle
        for vertex in self.vertexes:
            vertex.shuffle()

        # 4. mark crossed lines created above
        self.mark_crossed_lines()
        self.num_of_all_lines = len(self.lines)
        self.num_of_crossed_lines = self.num_of_crossed_lines_left


    def find_vertexes(self, pos):
        '''
        find the nearest vertex
        :param pos: the position of mouse cursor
        :return: the id of the selected vertex, -1 if no vertex is selected
        '''
        selected_id = -1  # -1 means no vertex is selected by default
        selected_dist = -1.  # distance between mouse and vertex

        for vertex in self.vertexes:
            dist = math.hypot(vertex.cur_pos[0] - pos[0], vertex.cur_pos[1] - pos[1])
            if selected_dist == -1 or selected_dist > dist:
                selected_dist = dist
                selected_id = vertex.index

        if selected_dist <= consts["vertex_size"]:
            return selected_id
        return -1

    def create_no_crossed_lines(self):
        '''
        generate no crossed lines for each vertex
        :return: None
        '''
        self.lines = []
        for i in range(self.num_of_vertexes):
            for j in range(i):
                crossed = False
                for l in self.lines:
                    if is_intersect(self.vertexes[i].cur_pos, self.vertexes[j].cur_pos,
                                    self.vertexes[l[0]].cur_pos, self.vertexes[l[1]].cur_pos):
                        crossed = True
                        break
                if not crossed:
                    self.lines.append([i, j, 0])


    def mark_crossed_lines(self):
        '''
        check all crossed lines if moving any vertex, set lines[][2] = 1 if the line is crossed
        :return: None
        '''
        self.num_of_crossed_lines_left = 0  # count of crossed lines
        for l in self.lines:
            l[2] = 0  # reset to no crossed status

        for i in range(len(self.lines) - 1):
            for j in range(i + 1, len(self.lines)):
                if is_intersect(self.vertexes[self.lines[i][0]].cur_pos, self.vertexes[self.lines[i][1]].cur_pos,
                                self.vertexes[self.lines[j][0]].cur_pos, self.vertexes[self.lines[j][1]].cur_pos):
                    self.lines[i][2] = self.lines[j][2] = 1   # the two lines are crossed each other

        for l in self.lines:
            if l[2] == 1:
                self.num_of_crossed_lines_left += 1


class Vertex:
    def __init__(self, rect, index, num_of_vertexes):
        self.rect = rect        # game area
        self.index = index      # the index [0..] of the vertex
        self.number = num_of_vertexes  # number of all vertexes
        self.end_pos = None     # game passed position (no crossed lines, generated at the beginning)
        self.cur_pos = None     # current position for drawing
        self.play_pos = None    # play position
        self.trigger = -1       # if 0: transform to end_pos; if 1: return back
        self.step = 0           # transform steps when trigger is True

    def generate(self):
        '''
        generate random position for the vertex(for to create no crossed lines)
        '''
        self.end_pos = [random.randint(self.rect.left, self.rect.right),
                        random.randint(self.rect.top, self.rect.bottom)]
        self.cur_pos = self.end_pos[:]

    def shuffle(self):
        '''
        reset to new game position (shuffle all vertexes to a circle)
        '''
        radius = min(self.rect.width, self.rect.height) * .3    # radius of the circle
        angle = math.pi * (2 * self.index / self.number + .5)        # .5 means the beginning angle is 90 degree
        self.play_pos = [round(self.rect.centerx + math.cos(angle) * radius),
                         round(self.rect.centery + math.sin(angle) * radius)]
        self.cur_pos = self.play_pos[:]

    def transform(self):  # call before drawing
        '''
        transform from play position to end position, or vice versa
        :return: null
        '''
        if self.trigger == -1:
            return
        if self.trigger == 0:    # transform from play_pos to end_pos
            self.step += .1
            self.cur_pos[0] += round((self.end_pos[0] - self.cur_pos[0]) * self.step)
            self.cur_pos[1] += round((self.end_pos[1] - self.cur_pos[1]) * self.step)
        elif self.trigger == 1:  # transform from end_pos to play_pos
            self.step += .1
            self.cur_pos[0] += round((self.play_pos[0] - self.cur_pos[0]) * self.step)
            self.cur_pos[1] += round((self.play_pos[1] - self.cur_pos[1]) * self.step)
        if self.step >= 1.:  # transforming finished
            self.step = 0
            self.trigger = -1


def draw_play_area(screen, gi):
    '''
    draw a single line between two vertexes
    :param screen:
    :param gi: instance of GameInfo()
    :return: none
    '''
    if gi.vertexes[0].trigger >= 0:
        for vertex in gi.vertexes:
            vertex.transform()

    gi.mark_crossed_lines()

    # draw anti-aliased lines
    for l in gi.lines:
        line_color = (l[2] == 1) and colors["crossed_line"] or colors["line"]
        pygame.draw.aaline(screen, line_color, gi.vertexes[l[0]].cur_pos, gi.vertexes[l[1]].cur_pos, True)

    # draw vertexes
    offset = screen_ball_r.get_width() // 2
    for vertex in gi.vertexes:
        crossed_lines_count = 0  # crossed lines count of the vertex
        all_lines_count = 0      # all lines count of the vertex
        for l in gi.lines:
            if l[0] == vertex.index or l[1] == vertex.index:
                crossed_lines_count += l[2]
                all_lines_count += 1
        if crossed_lines_count == 0:
            screen_ball = screen_ball_b  # no line is crossed line for the vertex
        elif crossed_lines_count == all_lines_count:
            screen_ball = screen_ball_r  # all lines are crossed line for the vertex
        else:
            screen_ball = screen_ball_y  # part of lines are crossed
        screen.blit(screen_ball, (vertex.cur_pos[0] - offset, vertex.cur_pos[1] - offset))

    # draw status text
    level_text = [" "]
    level_text.append("Level %d, %d/%d  %s" % (gi.level,
                                                gi.num_of_crossed_lines_left,
                                                gi.num_of_crossed_lines,
                                                langs["crossed_lines"]))
    if gi.num_of_crossed_lines_left == 0 and gi.finished is False and \
            gi.selected_id == -1 and gi.auto_move is False:
        gi.finished_time = time.time() - gi.start_time
        gi.finished = True

    if gi.finished:
        level_text.append("Finished in %d %s" % (gi.finished_time, langs["time_elapsed"]))
        level_text.append("")
        level_text.append("Click to the next level %d" % (gi.level + 1))
    else:
        level_text.append("%d %s" % (time.time() - gi.start_time, langs["time_elapsed"]))
    drawtext(screen, colors["text"], screen.get_rect(), level_text)


def drawtext(surface, font_color, rect, text):
    '''
    draw text in surface
    :param surface:
    :param font_color:
    :param rect: pygame.Rect to draw text
    :param text: multi-lines text[]
    :return: None
    '''
    font = pygame.font.SysFont('Axure Handwriting', 20, False)
    for t in text:
        text_surface = font.render(t, True, font_color)
        rect.left = (surface.get_width() - text_surface.get_width()) // 2
        rect.height = font.get_linesize()  # text height
        surface.blit(text_surface, rect)
        rect.top += rect.height


def on_segment(p, q, r):
    '''
    checks if point q lies on line segment "pr"
    '''
    if (q[0] < max(p[0], r[0]) and q[0] > min(p[0], r[0]) and
        q[1] < max(p[1], r[1]) and q[1] > min(p[1], r[1])):
        return True
    return False


def orientation(p, q, r):
    '''
    Find orientation of ordered triplet (p, q, r).
    :param p:
    :param q:
    :param r:
    :return:
    '''
    val = ((q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1]))
    if val == 0:
        return 0   # p, q and r are colinear
    elif val > 0:
        return 1   # clockwise
    else:
        return 2   # counter-clockwise


def is_intersect(p1, q1, p2, q2):
    '''
    check if the closed line segments p1-q1 and p2-q2 intersect
    :param p1:
    :param q1:
    :param p2:
    :param q2:
    :return:
    '''
    if p1 == p2 or p1 == q2 or q1 == p2 or q1 == q2:
        return False

    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if (o1 != o2 and o3 != o4):
        return True

    # Special Cases
    # p1, q1 and p2 are colinear and p2 lies on segment p1q1
    if (o1 == 0 and on_segment(p1, p2, q1)):
        return True

    # p1, q1 and p2 are colinear and q2 lies on segment p1q1
    if (o2 == 0 and on_segment(p1, q2, q1)):
        return True

    # p2, q2 and p1 are colinear and p1 lies on segment p2q2
    if (o3 == 0 and on_segment(p2, p1, q2)):
        return True

    # p2, q2 and q1 are colinear and q1 lies on segment p2q2
    if (o4 == 0 and on_segment(p2, q1, q2)):
        return True

    return False  # Doesn't fall in any of the above cases


# preload resource files
screen_wallpaper = pygame.image.load(resources["wallpaper"])
screen_ball_r = pygame.image.load(resources["ball_r"])   # red
screen_ball_y = pygame.image.load(resources["ball_y"])   # yellow
screen_ball_b = pygame.image.load(resources["ball_b"])   # blue


def main():
    # game init
    pygame.init()
    pygame.display.set_caption(langs["caption"])
    screen = pygame.display.set_mode(consts["screen_size"], 0, 32)
    # screen = pygame.display.set_mode(consts["screen_size"], pygame.FULLSCREEN |pygame.HWSURFACE, 32)
    game_rect = screen.get_rect().inflate(-consts["margin"] * 2, -consts["margin"] * 2)
    gi = GameInfo(game_rect)

    # post a new game event when launch
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": K_n, "mod": 0, "unicode": u' '}))

    while True:  # the main game loop
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            # start a new level
            elif event.type == pygame.KEYDOWN and event.key == K_n:
                gi.new_level(gi.level + 6)
                clip_pos = game_rect.height
                screen_fade_out = screen.copy()

            # reset the current game
            elif event.type == pygame.KEYDOWN and event.key == K_r:
                for vertex in gi.vertexes:
                    vertex.shuffle()

            # transform
            elif event.type == pygame.KEYDOWN and event.key == K_SPACE:
                # trigger transforming from end_pos to play_pos
                for vertex in gi.vertexes:
                    if vertex.trigger == -1:
                        vertex.trigger = 0 if gi.show_end_pos else 1
                gi.show_end_pos = not gi.show_end_pos
                gi.selected_id = -1
                gi.auto_move = True

            elif event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                if game_rect.collidepoint(pos) and gi.selected_id >= 0 and gi.finished is False:
                    gi.vertexes[gi.selected_id].cur_pos = [pos[0], pos[1]]
                    gi.vertexes[gi.selected_id].play_pos = gi.vertexes[gi.selected_id].cur_pos[:]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if gi.finished: # start a new game
                    pygame.event.clear()
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": K_n, "mod": 0, "unicode": u' '}))
                elif gi.show_end_pos:
                    gi.selected_id = gi.find_vertexes(pygame.mouse.get_pos())

            elif event.type == pygame.MOUSEBUTTONUP:
                gi.selected_id = -1
                gi.auto_move = False

        # fill screen buffer with background
        screen_new = screen.copy()
        screen_new.fill(gi.bk_color)

        draw_play_area(screen_new, gi)
        if clip_pos > 0:
            clip_pos //= 1.2
            screen.blit(screen_fade_out, (0, clip_pos - screen.get_height()))
        screen.blit(screen_new, (0, clip_pos))

        pygame.display.update()
        pygame.time.Clock().tick(consts["fps"])


if __name__ == '__main__':
    main()
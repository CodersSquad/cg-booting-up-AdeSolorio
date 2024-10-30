import math
import os
import sys

import numpy as np
import moderngl
import pygame
import glm
from objloader import Obj
from PIL import Image

os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

pygame.init()

pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 2)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

pygame.display.set_mode((800, 800), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)


class ImageTexture:
    def __init__(self, path):
        self.ctx = moderngl.get_context()
        img = Image.open(path).convert('RGBA')
        self.texture = self.ctx.texture(img.size, 4, img.tobytes())
        self.sampler = self.ctx.sampler(texture=self.texture)

    def use(self):
        self.sampler.use()


class ModelGeometry:
    def __init__(self, path):
        self.ctx = moderngl.get_context()
        obj = Obj.open(path)
        self.vbo = self.ctx.buffer(obj.pack('vx vy vz nx ny nz tx ty'))

    def vertex_array(self, program):
        return self.ctx.vertex_array(program, [(self.vbo, '3f 12x 2f', 'in_vertex', 'in_uv')])


class Mesh:
    def __init__(self, program, geometry, texture=None):
        self.ctx = moderngl.get_context()
        self.vao = geometry.vertex_array(program)
        self.texture = texture

    def render(self, position, color, scale):
        self.vao.program['position'] = position
        self.vao.program['color'] = color
        self.vao.program['scale'] = scale

        if self.texture:
            self.vao.program['use_texture'] = True
            self.texture.use()
        else:
            self.vao.program['use_texture'] = False

        self.vao.render()


class Scene:
    def __init__(self):
        self.ctx = moderngl.get_context()

        self.program = self.ctx.program(
            vertex_shader='''
                #version 150

                uniform mat4 camera;
                uniform vec3 position;
                uniform float scale;

                in vec3 in_vertex;
                in vec2 in_uv;

                out vec2 v_uv;

                void main() {
                    gl_Position = camera * vec4(position + in_vertex * scale, 1.0);
                    v_uv = -in_uv;  
                }
            ''',
            fragment_shader='''
                #version 150

                uniform sampler2D Texture;
                uniform bool use_texture;
                uniform vec3 color;

                in vec2 v_uv;

                out vec4 out_color;

                void main() {
                    out_color = vec4(color, 1.0);
                    if (use_texture) {
                        out_color *= texture(Texture, v_uv);
                    }
                }
            ''',
        )

        self.texture = ImageTexture('tec.jpg')
        self.car_geometry = ModelGeometry('lowpoly_toy_car.obj')
        self.car = Mesh(self.program, self.car_geometry)
        self.crate_geometry = ModelGeometry('crate.obj')
        self.crate = Mesh(self.program, self.crate_geometry, self.texture)

    def perspective(self, fov, aspect, near, far):
        return glm.perspective(glm.radians(fov), aspect, near, far)

    def camera_matrix(self):
        now = pygame.time.get_ticks() / 1000.0
        eye = glm.vec3(math.cos(now), math.sin(now), 0.5)
        look_at = glm.vec3(0.0, 0.0, 0.0)
        up = glm.vec3(0.0, 0.0, 1.0)
        proj = self.perspective(45.0, 1.0, 0.1, 1000.0)
        look = glm.lookAt(eye, look_at, up)
        return proj * look

    def render(self):
        camera = self.camera_matrix()
        self.ctx.clear()
        self.ctx.enable(self.ctx.DEPTH_TEST)
        self.program['camera'].write(camera)

        self.car.render((-0.4, 0.0, 0.0), (1.0, 0.0, 0.0), 0.2)
        self.crate.render((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 0.2)
        self.car.render((0.4, 0.0, 0.0), (0.0, 0.0, 1.0), 0.2)


scene = Scene()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    scene.render()
    pygame.display.flip()

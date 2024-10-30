import math
import os
import sys

import numpy as np
import moderngl
import pygame
import glm


# Set DPI awareness for high-resolution displays
os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

pygame.init()

# Set OpenGL context version to 3.2, which may be more compatible on M1 Macs
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 2)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

# Initialize the pygame display with OpenGL
pygame.display.set_mode((800, 800), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)


class TriangleGeometry:
    def __init__(self):
        self.ctx = moderngl.get_context()
        vertices = np.array([
            0.0, 0.4, 0.0,
            -0.4, -0.3, 0.0,
            0.4, -0.3, 0.0,
        ])

        self.vbo = self.ctx.buffer(vertices.astype('f4').tobytes())

    def vertex_array(self, program):
        return self.ctx.vertex_array(program, [(self.vbo, '3f', 'in_vertex')])


class Mesh:
    def __init__(self, program, geometry):
        self.ctx = moderngl.get_context()
        self.vao = geometry.vertex_array(program)

    def render(self, position, color, scale):
        self.vao.program['position'] = position
        self.vao.program['color'] = color
        self.vao.program['scale'] = scale
        self.vao.render()


class Scene:
    def __init__(self):
        self.ctx = moderngl.get_context()

        # Updated shader version to 150 for compatibility
        self.program = self.ctx.program(
            vertex_shader='''
                #version 150

                uniform mat4 camera;
                uniform vec3 position;
                uniform float scale;

                in vec3 in_vertex;

                void main() {
                    gl_Position = camera * vec4(position + in_vertex * scale, 1.0);
                }
            ''',
            fragment_shader='''
                #version 150

                uniform vec3 color;

                out vec4 out_color;

                void main() {
                    out_color = vec4(color, 1.0);
                }
            ''',
        )

        self.triangle_geometry = TriangleGeometry()
        self.triangle = Mesh(self.program, self.triangle_geometry)

    def perspective(self, fov, aspect, near, far):
        tan_half_fov = math.tan(math.radians(fov) / 2)
        z_range = near - far
        return np.array([
            [1 / (aspect * tan_half_fov), 0, 0, 0],
            [0, 1 / tan_half_fov, 0, 0],
            [0, 0, (near + far) / z_range, 2 * near * far / z_range],
            [0, 0, -1, 0]
        ], dtype=np.float32)

    def camera_matrix(self):
        now = pygame.time.get_ticks() / 1000.0
        eye = (math.cos(now), math.sin(now), 0.5)
        proj = self.perspective(45.0, 1.0, 0.1, 1000.0)
        look = glm.lookAt(eye, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        return proj @ look

    def render(self):
        camera = self.camera_matrix()

        self.ctx.clear()
        self.ctx.enable(self.ctx.DEPTH_TEST)

        self.program['camera'].write(camera)

        self.triangle.render((-0.2, 0.0, 0.0), (1.0, 0.0, 0.0), 0.2)
        self.triangle.render((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 0.2)
        self.triangle.render((0.2, 0.0, 0.0), (0.0, 0.0, 1.0), 0.2)


scene = Scene()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    scene.render()
    pygame.display.flip()
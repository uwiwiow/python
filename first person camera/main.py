import glfw
import glfw.GLFW as GLFW_CONSTANTS
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr


def createShader(vertexFilepath: str, fragmentFilepath: str) -> int:
    with open(vertexFilepath, 'r') as f:
        vertex_src = f.readlines()

    with open(fragmentFilepath, 'r') as f:
        fragment_src = f.readlines()

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                            compileShader(fragment_src, GL_FRAGMENT_SHADER))

    return shader


class Entity:

    def __init__(self, position: list[float], eulers: list[float]):
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

    def get_model_transform(self) -> np.ndarray:
        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        model_transform = pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_y_rotation(
                theta=np.radians(self.eulers[2]),
                dtype=np.float32
            )
        )

        model_transform = pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_translation(
                vec=self.position,
                dtype=np.float32
            )
        )

        return model_transform


class Triangle(Entity):

    def update(self, rate: float) -> None:
        self.eulers[2] += 0.25
        if self.eulers[2] > 360:
            self.eulers[2] -= 360


class Camera(Entity):

    def __init__(self, position: list[float], eulers: list[float]):
        super().__init__(position, eulers)

        # camera's fundamental directions
        self.localUp = np.array([0, 0, 1], dtype=np.float32)
        self.localRight = np.array([0, 1, 0], dtype=np.float32)
        self.localForwards = np.array([1, 0, 0], dtype=np.float32)

        # directions after roration
        self.up = np.array([0, 0, 1], dtype=np.float32)
        self.right = np.array([0, 1, 0], dtype=np.float32)
        self.forwards = np.array([1, 0, 0], dtype=np.float32)

    def calculate_vectors_rotation(self) -> None:
        cameraRotation = pyrr.matrix33.create_from_y_rotation(
            theta=np.radians(self.eulers[1]),
            dtype=np.float32
        )

        cameraRotation = pyrr.matrix33.multiply(
            m1=cameraRotation,
            m2=pyrr.matrix33.create_from_z_rotation(
                theta=np.radians(self.eulers[2]),
                dtype=np.float32
            )
        )

        self.up = pyrr.matrix33.multiply(
            m1=self.localUp,
            m2=cameraRotation
        )

        self.right = pyrr.matrix33.multiply(
            m1=self.localRight,
            m2=cameraRotation
        )

        self.forwards = pyrr.matrix33.multiply(
            m1=self.localForwards,
            m2=cameraRotation
        )

    def update(self) -> None:
        self.calculate_vectors_rotation()

    def get_view_transform(self) -> np.ndarray:
        return pyrr.matrix44.create_look_at(
            eye=self.position,
            target=self.position + self.forwards,
            up=self.up,
            dtype=np.float32
        )


class Scene:

    def __init__(self):

        self.triangle = Triangle(
            position=[3, 0, 0],
            eulers=[0, 0, 0]
        )

        self.camera = Camera(
            position=[0, 0, 0],
            eulers=[0, 0, 0]
        )

    def update(self, rate: float) -> None:

        self.triangle.update(rate)

        self.camera.update()

    def move_camera(self, dPos: np.ndarray) -> None:

        self.camera.position += dPos

    def spin_camera(self, dEulers: np.ndarray) -> None:

        self.camera.eulers += dEulers

        if self.camera.eulers[2] < 360:
            self.camera.eulers[2] += 360
        elif self.camera.eulers[2] > 360:
            self.camera.eulers[2] -= 360

        self.camera.eulers[1] = min(89, max(-89, self.camera.eulers[1]))


class App:

    def __init__(self):

        self.set_up_glfw()

        self.make_assets()

        self.set_onetime_unforms()

        self.get_uniform_locations()

        self.set_up_input_systems()

        self.set_up_timer()

        self.mainLoop()

    def set_up_glfw(self) -> None:

        self.screenWidth = 640
        self.screenHeight = 480

        glfw.init()
        glfw.window_hint(GLFW_CONSTANTS.GLFW_CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(GLFW_CONSTANTS.GLFW_CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(
            GLFW_CONSTANTS.GLFW_OPENGL_FORWARD_COMPAT,
            GLFW_CONSTANTS.GLFW_TRUE
        )
        glfw.window_hint(GLFW_CONSTANTS.GLFW_DOUBLEBUFFER, False)
        self.window = glfw.create_window(
            self.screenWidth, self.screenHeight, "First person camera", None, None
        )
        glfw.make_context_current(self.window)

    def make_assets(self) -> None:
        self.scene = Scene()
        self.triangle_mesh = TriangleMesh()
        self.shader = createShader("shaders/vertex.txt", "shaders/fragment.txt")

    def set_onetime_unforms(self) -> None:
        glUseProgram(self.shader)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy=45,
            aspect=self.screenWidth / self.screenHeight,
            near=0.1, far=10, dtype=np.float32
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "projection"),
            1, GL_FALSE, projection_transform
        )

    def get_uniform_locations(self) -> None:

        glUseProgram(self.shader)
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")

    def set_up_input_systems(self) -> None:

        glfw.set_input_mode(
            self.window,
            GLFW_CONSTANTS.GLFW_CURSOR,
            GLFW_CONSTANTS.GLFW_CURSOR_HIDDEN
        )

        glfw.set_cursor_pos(
            self.window,
            self.screenWidth // 2,
            self.screenHeight // 2
        )

        self.walk_offset_lookup = {
            1: 0,
            2: 90,
            3: 45,
            4: 180,
            6: 135,
            7: 90,
            8: 270,
            9: 315,
            11: 0,
            12: 225,
            13: 270,
            14: 180
        }

    def set_up_timer(self) -> None:

        self.lastTime = glfw.get_time()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0

    def mainLoop(self) -> None:
        # run the app

        glClearColor(0.00, 0.33, 0.50, 1)
        (w, h) = glfw.get_framebuffer_size(self.window)
        glViewport(0, 0, w, h)

        running = True
        while (running):
            # check for events
            if glfw.window_should_close(self.window) \
                    or glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_ESCAPE) == GLFW_CONSTANTS.GLFW_PRESS:
                running = False

            self.handleKeys()
            self.handleMouse()

            glfw.poll_events()

            # update scene
            self.scene.update(self.frameTime / 16.667)

            # refresh screen
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(self.shader)

            glUniformMatrix4fv(
                self.viewMatrixLocation,
                1, GL_FALSE,
                self.scene.camera.get_view_transform()
            )

            glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, self.scene.triangle.get_model_transform())

            # draw the triangle
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            glFlush()
            # timing
            self.calculateFramerate()

        self.quit()

    def handleKeys(self) -> None:

        combo = 0
        directionModifier = 0

        if glfw.get_key(
                self.window, GLFW_CONSTANTS.GLFW_KEY_W
        ) == GLFW_CONSTANTS.GLFW_PRESS:
            combo += 1
        elif glfw.get_key(
                self.window, GLFW_CONSTANTS.GLFW_KEY_A
        ) == GLFW_CONSTANTS.GLFW_PRESS:
            combo += 2
        elif glfw.get_key(
                self.window, GLFW_CONSTANTS.GLFW_KEY_S
        ) == GLFW_CONSTANTS.GLFW_PRESS:
            combo += 4
        elif glfw.get_key(
                self.window, GLFW_CONSTANTS.GLFW_KEY_D
        ) == GLFW_CONSTANTS.GLFW_PRESS:
            combo += 8

        if combo in self.walk_offset_lookup:
            directionModifier = self.walk_offset_lookup[combo]
            rate = self.frameTime / 16.667

            dPos = 0.1 * rate * np.array(
                [
                    np.cos(np.deg2rad(self.scene.camera.eulers[2] + directionModifier)),
                    np.sin(np.deg2rad(self.scene.camera.eulers[2] + directionModifier)),
                    0
                ],
                dtype=np.float32
            )

            self.scene.move_camera(dPos)

    def handleMouse(self) -> None:

        (x, y) = glfw.get_cursor_pos(self.window)
        rate = self.frameTime / 16.667
        theta_increment = rate * ((self.screenWidth / 2.0) - x)
        phi_increment = - rate * ((self.screenHeight / 2.0) - y)
        dEulers = np.array([0, phi_increment, theta_increment], dtype=np.float32)
        self.scene.spin_camera(dEulers)
        glfw.set_cursor_pos(self.window, self.screenWidth // 2, self.screenHeight // 2)

    def calculateFramerate(self) -> None:

        self.currentTime = glfw.get_time()
        delta = self.currentTime - self.lastTime
        if (delta >= 1):
            framerate = int(self.numFrames / delta)
            glfw.set_window_title(self.window, f"Running at {framerate} fps.")
            self.lastTime = self.currentTime
            self.numFrames = -1
            self.frameTime = float(1000.0 / max(144, framerate))
        self.numFrames += 1

    def quit(self) -> None:

        self.triangle_mesh.destroy()
        glDeleteProgram(self.shader)
        glfw.terminate()


class TriangleMesh:

    def __init__(self):
        # x, y, z, r, g, b
        self.vertices = (
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
            0.5, -0.5, 0.0, 0.0, 1.0, 0.0,
            0.0, 0.5, 0.0, 0.0, 0.0, 1.0
        )

        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vertex_count = 3

        self.vao = glGenVertexArrays(1)  # vao = vortex array object
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)  # vbo = vertex buffer object
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices,
                     GL_STATIC_DRAW)  # subiendo a el buffer de la memoria los datos, el vbo

        print(f"Vertex Array Handle {self.vao}")  # identificadores como indeces de los objetos
        print(f"Buffer Handle {self.vbo}")  # vvvvv
        buffer_size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        print(
            f"Our buffer is taking up {buffer_size} bytes in memory")  # memoria del buffer, 9 puntos tipo float, de 4 bytes c/u = 36 bytes en buffer

        glEnableVertexAttribArray(
            0)  # tambien funciona glEnableVertexAttribArray que solo funciona con un parametro y es mas nuevo (o eso creo | video 1:04:30)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))


if __name__ == "__main__":
    myApp = App()

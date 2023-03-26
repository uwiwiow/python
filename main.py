import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr

def createShader(vertexFilepath: str, fragmentFilepath: str) -> int:
    
    with open(vertexFilepath,'r') as f:
        vertex_src = f.readlines()

    with open(fragmentFilepath,'r') as f:
        fragment_src = f.readlines()

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

    return shader

class Entity:

    def __init__(self, position: list[float], eulers: list[float]):
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        
    def make_model_transform(self) -> np.ndarray:
        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        model_transform = pyrr.matrix44.multiply(
            m1 = model_transform,
            m2 = pyrr.matrix44.create_from_y_rotation(
                theta=np.radians(self.eulers[2]),
                dtype=np.float32
            )
        )

        model_transform = pyrr.matrix44.multiply(
            m1 = model_transform,
            m2 = pyrr.matrix44.create_from_translation(
                vec=self.position,
                dtype=np.float32
            )
        )

        return model_transform
    

class App:

    def __init__(self):        
        self.set_up_pygame()

        self.make_assets()

        self.set_onetime_unforms()

        self.get_uniform_locations()

        self.mainLoop()

    def set_up_pygame(self) -> None:
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)

        pg.display.set_mode((640, 480), pg.OPENGL|pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        
    def make_assets(self) -> None:

        self.triangle_mesh = TriangleMesh()

        self.triangle = Entity(
            position= [0.0, 0.0, -2.0],
            eulers=[0,0,0]
            )
        
        self.shader = createShader("shaders/vertex.txt", "shaders/fragment.txt")

    def get_uniform_locations(self) -> None:

        glUseProgram(self.shader)

        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")

    def set_onetime_unforms(self) -> None:
        glUseProgram(self.shader)

        projection_transform = pyrr.matrix44.create_perspective_projection(90, 640/480, 0.1, 10.0, dtype=np.float32)

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "projection"),
            1, GL_FALSE, projection_transform
        )



    def mainLoop(self) -> None:
        #run the app

        glClearColor(0.00, 0.33, 0.50, 1)
        running = True
        while (running):
            #check for events
            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False

            #update triangle
            self.triangle.eulers[2] += 0.25
            if self.triangle.eulers[2] > 360:
                self.triangle.eulers[2] -= 360

            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(self.shader)

            
            glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, self.triangle.make_model_transform())

            #draw the triangle
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)



            pg.display.flip()
            #timing
            self.clock.tick(144)

        self.quit()

    def quit(self) -> None:
        self.triangle_mesh.destroy()
        glDeleteProgram(self.shader)
        pg.quit()
        
class TriangleMesh:

    def __init__(self):
        
        # x, y, z, r, g, b
        self.vertices = (
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
             0.5, -0.5, 0.0, 0.0, 1.0, 0.0,
             0.0,  0.5, 0.0, 0.0, 0.0, 1.0
        )

        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vertex_count = 3

        self.vao = glGenVertexArrays(1) #vao = vortex array object
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1) #vbo = vertex buffer object
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)  #subiendo a el buffer de la memoria los datos, el vbo


        print(f"Vertex Array Handle {self.vao}") #identificadores como indeces de los objetos
        print(f"Buffer Handle {self.vbo}") # vvvvv
        buffer_size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        print(f"Our buffer is taking up {buffer_size} bytes in memory") #memoria del buffer, 9 puntos tipo float, de 4 bytes c/u = 36 bytes en buffer

        glEnableVertexAttribArray(0) #tambien funciona glEnableVertexAttribArray que solo funciona con un parametro y es mas nuevo (o eso creo | video 1:04:30)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))


if __name__ == "__main__":

    myApp = App()
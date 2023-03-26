import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr

def createShader(vertexFilepath, fragmentFilepath):
    
    with open(vertexFilepath,'r') as f:
        vertex_src = f.readlines()

    with open(fragmentFilepath,'r') as f:
        fragment_src = f.readlines()

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

    return shader

class Entity:

    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

class App:

    def __init__(self):        
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)

        pg.display.set_mode((1920, 1080), pg.OPENGL|pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        glClearColor(0.00, 0.33, 0.50, 1)

        self.triangle_mesh = TriangleMesh()
        self.triangle_mesh_2 = TriangleMesh_2()
        self.shader = createShader("triangle_shaders/vertex.txt", "triangle_shaders/fragment.txt")
        glUseProgram(self.shader)

        self.triangle = Entity(position= [0.5, 0, 0], eulers=[0,0,0])

        self.mainLoop()

    def mainLoop(self) -> None:
        #run the app
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

            self.triangle.eulers[1] -= 0.25
            if self.triangle.eulers[1] > 360:
                self.triangle.eulers[1] += 360

            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(self.shader)

            model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
            model_transform_2 = pyrr.matrix44.create_identity(dtype=np.float32)

            model_transform = pyrr.matrix44.multiply(
                m1 = model_transform,
                m2 = pyrr.matrix44.create_from_z_rotation(theta = np.radians(self.triangle.eulers[2]), dtype=np.float32)
            )
            

            model_transform = pyrr.matrix44.multiply(
                m1 = model_transform,
                m2 = pyrr.matrix44.create_from_y_rotation(theta = np.radians(self.triangle.eulers[2]), dtype=np.float32)
            )

            model_transform = pyrr.matrix44.multiply(
                m1 = model_transform,
                m2 = pyrr.matrix44.create_from_x_rotation(theta = np.radians(self.triangle.eulers[2]), dtype=np.float32)
            )

            model_transform = pyrr.matrix44.multiply(
                m1 = model_transform,
                m2 = pyrr.matrix44.create_from_translation(vec = np.array([0.0, 0.0, 0.0]), dtype=np.float32)
            )

            self.triangle_mesh.build_vertices(model_transform)
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            model_transform_2 = pyrr.matrix44.multiply(
                m1 = model_transform_2,
                m2 = pyrr.matrix44.create_from_y_rotation(theta = np.radians(self.triangle.eulers[2]), dtype=np.float32)
            )

            model_transform_2 = pyrr.matrix44.multiply(
                m1 = model_transform_2,
                m2 = pyrr.matrix44.create_from_z_rotation(theta = np.radians(self.triangle.eulers[2]), dtype=np.float32)
            )

            model_transform_2 = pyrr.matrix44.multiply(
                m1 = model_transform_2,
                m2 = pyrr.matrix44.create_from_x_rotation(theta = np.radians(self.triangle.eulers[2]), dtype=np.float32)
            )

            model_transform_2 = pyrr.matrix44.multiply(
                m1 = model_transform_2,
                m2 = pyrr.matrix44.create_from_translation(vec = np.array([0.0, 0.0, 0.0]), dtype=np.float32)
            )

            self.triangle_mesh_2.build_vertices(model_transform_2)
            glBindVertexArray(self.triangle_mesh_2.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh_2.vertex_count)



            pg.display.flip()
            #timing
            self.clock.tick(144)

        self.quit()

    def quit(self) -> None:
        self.triangle_mesh.destroy()
        self.triangle_mesh_2.destroy()
        glDeleteProgram(self.shader)
        pg.quit()
        
class TriangleMesh:

    def __init__(self):
        
        self.originalPositions = (
            pyrr.vector4.create(-0.5, -0.5, 0.0, 1.0, dtype=np.float32),
            pyrr.vector4.create( 0.5, -0.5, 0.0, 1.0, dtype=np.float32),
            pyrr.vector4.create( 0.0,  0.5, 0.0, 1.0, dtype=np.float32)
        )

        self.originalColors = (
            pyrr.vector3.create( 1.0, 0.0, 0.0, dtype=np.float32),
            pyrr.vector3.create( 0.0, 1.0, 0.0, dtype=np.float32),
            pyrr.vector3.create( 0.0, 0.0, 1.0, dtype=np.float32)
        )

        self.vertex_count = 3

        self.vao = glGenVertexArrays(1) #vao = vortex array object
        self.vbo = glGenBuffers(1) #vbo = vertex buffer object

        self.build_vertices(pyrr.matrix44.create_identity(dtype=np.float32))

        
        print(f"Vertex Array Handle {self.vao}") #identificadores como indeces de los objetos
        print(f"Buffer Handle {self.vbo}") # vvvvv
        buffer_size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        print(f"Our buffer is taking up {buffer_size} bytes in memory") #memoria del buffer, 9 puntos tipo float, de 4 bytes c/u = 36 bytes en buffer

        glEnableVertexArrayAttrib(self.vao, 0) #tambien funciona glEnableVertexAttribArray que solo funciona con un parametro y es mas nuevo (o eso creo | video 1:04:30)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        glEnableVertexArrayAttrib(self.vao, 1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def build_vertices(self, transform: np.ndarray) -> None:

        self.vertices = np.array([], dtype=np.float32)

        for i in range(self.vertex_count):
            
            transform_position = pyrr.matrix44.multiply(
                m1 = self.originalPositions[i],
                m2 = transform
            )

            self.vertices = np.append(self.vertices, transform_position[0:3])
            self.vertices = np.append(self.vertices, self.originalColors[i])



        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)  #subiendo a el buffer de la memoria los datos, el vbo

    def destroy(self):

        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))



class TriangleMesh_2:

    def __init__(self):
        
        self.originalPositions = (
            pyrr.vector4.create(-0.5,  0.5, 0.0, 1.0, dtype=np.float32),
            pyrr.vector4.create( 0.5,  0.5, 0.0, 1.0, dtype=np.float32),
            pyrr.vector4.create( 0.0, -0.5, 0.0, 1.0, dtype=np.float32)
        )

        self.originalColors = (
            pyrr.vector3.create( 1.0, 0.0, 0.0, dtype=np.float32),
            pyrr.vector3.create( 0.0, 1.0, 0.0, dtype=np.float32),
            pyrr.vector3.create( 0.0, 0.0, 1.0, dtype=np.float32)
        )

        self.vertex_count = 3

        self.vao = glGenVertexArrays(1) #vao = vortex array object
        self.vbo = glGenBuffers(1) #vbo = vertex buffer object

        self.build_vertices(pyrr.matrix44.create_identity(dtype=np.float32))

        
        print(f"Vertex Array Handle {self.vao}") #identificadores como indeces de los objetos
        print(f"Buffer Handle {self.vbo}") # vvvvv
        buffer_size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        print(f"Our buffer is taking up {buffer_size} bytes in memory") #memoria del buffer, 9 puntos tipo float, de 4 bytes c/u = 36 bytes en buffer

        glEnableVertexArrayAttrib(self.vao, 0) #tambien funciona glEnableVertexAttribArray que solo funciona con un parametro y es mas nuevo (o eso creo | video 1:04:30)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        glEnableVertexArrayAttrib(self.vao, 1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def build_vertices(self, transform: np.ndarray) -> None:

        self.vertices = np.array([], dtype=np.float32)

        for i in range(self.vertex_count):
            
            transform_position = pyrr.matrix44.multiply(
                m1 = self.originalPositions[i],
                m2 = transform
            )

            self.vertices = np.append(self.vertices, transform_position[0:3])
            self.vertices = np.append(self.vertices, self.originalColors[i])



        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)  #subiendo a el buffer de la memoria los datos, el vbo

    def destroy(self):

        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))


if __name__ == "__main__":
    myApp = App()
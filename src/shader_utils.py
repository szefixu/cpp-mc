from OpenGL.GL import *

def load_shader_source(filepath: str) -> str:
    """
    Loads shader source code from a file.

    Args:
        filepath (str): The path to the shader file.

    Returns:
        str: The shader source code as a string.

    Raises:
        FileNotFoundError: If the shader file cannot be found.
        Exception: For other potential I/O errors.
    """
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        return source
    except FileNotFoundError:
        print(f"Error: Shader file not found at '{filepath}'")
        raise
    except Exception as e:
        print(f"Error loading shader file '{filepath}': {e}")
        raise

def compile_shader(source: str, shader_type: GLenum) -> int:
    """
    Compiles a shader from source code.

    Args:
        source (str): The shader source code.
        shader_type (GLenum): The type of shader (e.g., GL_VERTEX_SHADER, GL_FRAGMENT_SHADER).

    Returns:
        int: The ID of the compiled shader.

    Raises:
        Exception: If shader compilation fails.
    """
    shader = glCreateShader(shader_type)
    if not shader:
        raise RuntimeError("Unable to create shader object")
        
    glShaderSource(shader, source)
    glCompileShader(shader)

    compile_status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if not compile_status:
        info_log = glGetShaderInfoLog(shader)
        glDeleteShader(shader) # Clean up the shader object
        error_message = f"Shader compilation failed (type {shader_type}):\n{info_log.decode()}"
        print(error_message)
        raise Exception(error_message)
    
    return shader

def create_shader_program(vertex_shader_filepath: str, fragment_shader_filepath: str) -> int:
    """
    Creates a shader program from vertex and fragment shader files.

    Args:
        vertex_shader_filepath (str): Path to the vertex shader source file.
        fragment_shader_filepath (str): Path to the fragment shader source file.

    Returns:
        int: The ID of the created shader program.

    Raises:
        Exception: If loading, compiling, or linking shaders fails.
    """
    # Load shader sources
    vertex_source = load_shader_source(vertex_shader_filepath)
    fragment_source = load_shader_source(fragment_shader_filepath)

    # Compile shaders
    vertex_shader_id = compile_shader(vertex_source, GL_VERTEX_SHADER)
    fragment_shader_id = compile_shader(fragment_source, GL_FRAGMENT_SHADER)

    # Create shader program
    program = glCreateProgram()
    if not program:
        # Clean up individual shaders if program creation fails
        glDeleteShader(vertex_shader_id)
        glDeleteShader(fragment_shader_id)
        raise RuntimeError("Unable to create shader program object")

    glAttachShader(program, vertex_shader_id)
    glAttachShader(program, fragment_shader_id)
    glLinkProgram(program)

    # Check for linking errors
    link_status = glGetProgramiv(program, GL_LINK_STATUS)
    if not link_status:
        info_log = glGetProgramInfoLog(program)
        # Clean up before raising
        glDetachShader(program, vertex_shader_id)
        glDetachShader(program, fragment_shader_id)
        glDeleteShader(vertex_shader_id)
        glDeleteShader(fragment_shader_id)
        glDeleteProgram(program)
        error_message = f"Shader program linking failed:\n{info_log.decode()}"
        print(error_message)
        raise Exception(error_message)

    # Detach and delete individual shaders as they are now linked into the program
    glDetachShader(program, vertex_shader_id)
    glDetachShader(program, fragment_shader_id)
    glDeleteShader(vertex_shader_id)
    glDeleteShader(fragment_shader_id)

    return program

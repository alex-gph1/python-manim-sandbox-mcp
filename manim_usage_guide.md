# Manim Animation Tools Usage Guide

## Overview
The sandbox provides dedicated tools for creating Manim animations with automatic artifact management and tracking.

## Tool: `create_manim_animation`

### Parameters
- **`manim_code`** (required): Python code containing Manim scene definition and animations

### Common Errors and Solutions

1. **Error**: `'manim_code' is a required property`
   - **Solution**: Always include the `manim_code` parameter
   - **Incorrect**: `{"output_name": "my_animation", "scene_name": "MyScene"}`
   - **Correct**: `{"manim_code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        pass"}`

2. **Error**: `Unexpected keyword argument`
   - **Solution**: Only use `manim_code` parameter. Do not use `output_name`, `scene_name`, or other parameters
   - **Incorrect**: `{"manim_code": "...", "output_name": "test"}`
   - **Correct**: `{"manim_code": "..."}`

3. **Error**: `No scenes inside that module`
   - **Solution**: Ensure your code defines a class that inherits from Scene
   - **Incorrect**: `{"manim_code": "from manim import *\ncircle = Circle()"}`
   - **Correct**: `{"manim_code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        circle = Circle()\n        self.play(Create(circle))"}`

## Basic Usage Examples

### 1. Simple Circle Animation
```python
{
    "manim_code": "from manim import *\n\nclass CircleAnimation(Scene):\n    def construct(self):\n        circle = Circle(radius=2, color=BLUE)\n        self.play(Create(circle))\n        self.play(circle.animate.set_color(RED))\n        self.wait(1)"
}
```

### 2. Text and Shapes
```python
{
    "manim_code": "from manim import *\n\nclass TextAndShapes(Scene):\n    def construct(self):\n        title = Text('Hello Manim!', font_size=48)\n        square = Square(side_length=3, color=GREEN)\n        \n        self.play(Write(title))\n        self.play(title.animate.to_edge(UP))\n        self.play(Create(square))\n        self.play(square.animate.rotate(PI/4))\n        self.wait(2)"
}
```

### 3. Mathematical Animations
```python
{
    "manim_code": "from manim import *\n\nclass MathAnimation(Scene):\n    def construct(self):\n        equation = MathTex(r'e^{i\\pi} + 1 = 0')\n        self.play(Write(equation))\n        self.play(equation.animate.scale(2))\n        self.wait(1)\n        \n        # Transform to another equation\n        new_eq = MathTex(r'\\frac{d}{dx}x^2 = 2x')\n        self.play(Transform(equation, new_eq))\n        self.wait(2)"
}
```

### 4. 3D Animation
```python
{
    "manim_code": "from manim import *\n\nclass ThreeDExample(ThreeDScene):\n    def construct(self):\n        axes = ThreeDAxes()\n        cube = Cube(side_length=2, color=BLUE)\n        \n        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)\n        self.play(Create(axes))\n        self.play(Create(cube))\n        self.play(Rotate(cube, angle=PI, axis=UP))\n        self.wait(2)"
}
```

## Output and Artifacts

### Successful Response Structure
```json
{
    "success": true,
    "output": "Manim execution log...",
    "error": null,
    "video_path": "/path/to/final/video.mp4",
    "animation_id": "unique_id",
    "artifacts_dir": "/path/to/artifacts/directory",
    "scenes_found": [],
    "execution_time": 2.5,
    "warning": null
}
```

### Artifact Organization
When an animation is created, artifacts are organized as follows:
```
artifacts/
└── session_YYYYMMDD_HHMMSS_sessionid/
    └── manim_animationid/
        ├── scene.py                    # Your scene code
        ├── __pycache__/               # Python cache files
        └── media/
            ├── videos/
            │   └── scene/
            │       └── 720p30/
            │           ├── SceneName.mp4           # Final video
            │           └── partial_movie_files/    # Intermediate files
            └── texts/                             # Generated text SVGs
```

### Key Artifact Files
- **Final Video**: `media/videos/scene/720p30/YourSceneName.mp4`
- **Source Code**: `scene.py`
- **Partial Videos**: Individual animation segments in `partial_movie_files/`
- **Text Assets**: SVG files for text elements in `media/texts/`

## Best Practices

1. **Always include imports**: Start with `from manim import *`
2. **Use descriptive scene names**: Class names become the video filename
3. **Add wait times**: Use `self.wait()` for better pacing
4. **Test simple animations first**: Start with basic shapes before complex scenes
5. **Check artifacts after creation**: Use `list_artifacts` to verify output

## Troubleshooting

### Scene Not Found
- Ensure your class inherits from `Scene`, `ThreeDScene`, or similar
- Check that the class name follows Python naming conventions
- Verify proper indentation in the `construct` method

### Import Errors
- Always start with `from manim import *`
- For specific imports, use `from manim import Scene, Circle, Create, etc.`

### Animation Errors
- Check Manim documentation for correct animation syntax
- Ensure objects are created before animating them
- Use `self.play()` for animations and `self.add()` for static objects

## Example Workflow

1. **Create Animation**:
   ```python
   call_mcp_tool("create_manim_animation", {
       "manim_code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        circle = Circle()\n        self.play(Create(circle))"
   })
   ```

2. **Check Artifacts**:
   ```python
   call_mcp_tool("list_artifacts", {})
   ```

3. **Locate Video**:
   - Look for `.mp4` file in the response
   - Video path will be in `video_path` field
   - Full artifact structure available via `list_artifacts`

This guide should eliminate common errors and provide clear direction for creating Manim animations in the sandbox environment.

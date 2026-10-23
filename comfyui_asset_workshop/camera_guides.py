"""Known cameras in the saved GLB frame; no image-based pose estimation."""
import math


def pixal_camera(camera):
    """Convert the renderer's Y-up look-at frame to Pixal's Z-up c2w."""
    def cross(a,b):
        return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    def unit(v):
        length=math.sqrt(sum(x*x for x in v))
        if not math.isfinite(length) or length < 1e-8:
            raise ValueError("The requested camera basis is degenerate.")
        return [x/length for x in v]
    eye,target=camera["position"],camera["target"]
    forward=unit([b-a for a,b in zip(eye,target)])
    up=[0,1,0] if abs(forward[1]) < .99 else [0,0,1]
    right=unit(cross(forward,up))
    up=cross(right,forward)
    # Apply the same world rotation used by native Pixal projection to each
    # basis vector and the full eye position (including target offset).
    columns=[[v[0],-v[2],v[1]] for v in (right,up,[-x for x in forward],eye)]
    return [[v[row] for v in columns] for row in range(3)]+[[0,0,0,1]]


def orbit(draft, pose, size=1024):
    low, high = draft["bounds_min"], draft["bounds_max"]
    if len(low) != 3 or len(high) != 3 or not all(math.isfinite(v) for v in (*low, *high)):
        raise ValueError("The draft bounds are invalid. Rebuild its shape.")
    if any(a > b for a, b in zip(low, high)):
        raise ValueError("The draft bounds are inverted.")
    target = [(a+b)*.5 for a,b in zip(low,high)]
    radius = math.sqrt(sum(((b-a)*.5)**2 for a,b in zip(low,high)))
    azimuth, elevation, fov = (float(pose[key]) for key in ("azimuth", "elevation", "fov"))
    if not all(math.isfinite(v) for v in (azimuth,elevation,fov)) or not -90 <= elevation <= 90 or not 2 <= fov <= 120 or radius <= 0:
        raise ValueError("Camera guides need a nonempty draft, elevation -90 to 90 and field of view 2 to 120 degrees.")
    # A bounding sphere fits every angle without a different per-view crop.
    # sin (rather than tan) also leaves the near side of the sphere in frame.
    distance = radius / math.sin(math.radians(fov)*.5) * 1.05
    az, el = math.radians(-azimuth), math.radians(elevation)
    offset = (math.sin(az)*math.cos(el), math.sin(el), math.cos(az)*math.cos(el))
    position = [p + distance*d for p,d in zip(target,offset)]
    if any(abs(v) > 1000 for v in (*position,*target)):
        raise ValueError("The draft exceeds the native camera range. Check its scale before making guides.")
    return {"position":position, "target":target, "distance":distance, "radius":radius,
            "fov":fov, "zoom":1, "projection":"perspective", "size":[size,size], "crop":False,
            "frame":"glTF Y-up; front +Z; object right -X; roll-free; pole up +Z",
            "depth":"per-view relative depth; near white, far black; background black",
            "normal":"native RenderMesh view-space OpenGL normals mapped to RGB; X right, Y up, Z toward camera",
            "pose_source":"known draft render; generated images still require visual review"}

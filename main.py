import json
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import pygame.freetype
import random

pygame.init()

PARTICLE_SIZE = 3
GEN_BORDER = 1
particle_grid = {}
X_RANDOM = 2

WIDTH = (801 // PARTICLE_SIZE) * PARTICLE_SIZE
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Particles')

mouse = [0, 0, 0]

active = 0
particle_types = [
    {'color': (0, 0, 255), 'gravity': 'liquid', 'name': 'water'},
    {'color': (100, 45, 0), 'gravity': 'liquid', 'name': 'oil', 'combustibility': 100},
    {'color': (169, 169, 169), 'gravity': 'powder', 'name': 'gunpowder', 'combustibility': 200},
    {'color': (255, 0, 0), 'gravity': 'fire', 'name': 'fire'},
    {'color': (150, 150, 150), 'gravity': 'solid', 'name': 'block'},
    {'color': (150, 100, 50), 'gravity': 'solid', 'name': 'wood', 'combustibility': 100},
    {'color': (255, 255, 0), 'gravity': 'gen', 'name': 'generator'},
    {'color': (0, 255, 0), 'gravity': 'liquid', 'name': 'acid'},
    {'color': (0, 0, 0), 'gravity': 'erase', 'name': 'erase'},
]

SMALL_FONT = pygame.freetype.Font("font.ttf", 20)


def draw_ui():
    """Draws the UI elements like the active particle indicator."""
    toolbar_width = 200
    padding = 10
    active_padding = 4
    icon_size = 30

    pygame.draw.rect(screen, (50, 50, 50), (padding, padding, toolbar_width, padding + (padding + icon_size) * 3))

    for index, particle_type in enumerate([particle_types[active - 1], particle_types[active], particle_types[(active + 1) if active < len(particle_types) - 1 else 0]]):
        x = padding * 2
        y = padding * 2 + index * (icon_size + padding)
        if particle_type == particle_types[active]:  # Highlight the currently selected particle
            pygame.draw.rect(screen, (255, 255, 255), (x, y, icon_size, icon_size))
            pygame.draw.rect(screen, particle_type['color'], (x + active_padding, y + active_padding, icon_size - active_padding * 2, icon_size -  active_padding * 2))
        else:
            pygame.draw.rect(screen, particle_type['color'], (x, y, icon_size, icon_size))
        SMALL_FONT.render_to(screen, (x + icon_size + padding, y + icon_size / 2 - 8, 350), particle_type['name'], (255, 255, 255))


def handle_events():
    """Handles user input and updates the mouse and active state."""
    global active
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse[2] = 1
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse[2] = 0
        elif event.type == pygame.MOUSEMOTION:
            update_mouse_position()
        elif event.type == pygame.KEYUP:
            handle_keys(event.key)


def update_mouse_position():
    """Updates the mouse position aligned to the particle grid."""
    mouse[0] = pygame.mouse.get_pos()[0] - pygame.mouse.get_pos()[0] % PARTICLE_SIZE
    mouse[1] = pygame.mouse.get_pos()[1] - pygame.mouse.get_pos()[1] % PARTICLE_SIZE


def apply_mouse_interaction():
    """Handles adding or erasing particles based on mouse interaction."""
    if not mouse[2]:
        return
    if particle_types[active]['gravity'] == 'erase':
        erase_particles(mouse[0], mouse[1])
        return
    add_particles_in_area(mouse[0], mouse[1])


def get_next_file(filename_prefix="particle", extension=".txt"):
    """
    Finds the next available filename with incremental numbers (e.g., particle1.txt, particle2.txt).
    """
    i = 1
    while os.path.exists(f"{filename_prefix}{i}{extension}"):
        i += 1
    return f"{filename_prefix}{i}{extension}"


def get_latest_file(filename_prefix="particle", extension=".txt"):
    """
    Finds the latest file with the specified prefix and extension (e.g., particle1.txt, particle2.txt).
    Returns None if no files are found.
    """
    i = 1
    latest_file = None
    while os.path.exists(f"{filename_prefix}{i}{extension}"):
        latest_file = f"{filename_prefix}{i}{extension}"
        i += 1
    return latest_file


def tuple_keys_to_strings(grid):
    """Converts tuple keys in a dictionary to strings."""
    return {str(k): v for k, v in grid.items()}


def string_keys_to_tuples(grid):
    """Converts string keys in a dictionary back to tuples."""
    return {tuple(map(int, k.strip("()").split(", "))): v for k, v in grid.items()}


def handle_keys(key):
    """Handles keyboard input."""
    global active, particle_grid
    if key == pygame.K_LEFT:
        active -= 1
        if active == -1:
            active = len(particle_types) - 1
    elif key == pygame.K_RIGHT:
        active += 1
        if active == len(particle_types):
            active = 0
    elif key == pygame.K_s:
        filename = get_next_file()
        with open(filename, 'w') as file:
            json.dump(tuple_keys_to_strings(particle_grid), file)
        print(f"Saved particle grid to {filename}")
    elif key == pygame.K_l:
        filename = get_latest_file()
        if filename:
            with open(filename, 'r') as file:
                loaded_grid = json.load(file)
                particle_grid = string_keys_to_tuples(loaded_grid)
            print(f"Loaded particle grid from {filename}")
        else:
            print("No particle configuration files found.")


def is_occupied(x, y):
    """Checks if a position is occupied in the particle grid."""
    return (x, y) in particle_grid


def get_neighbors(x, y):
    """Returns the neighboring positions of a particle."""
    return [
        (x - PARTICLE_SIZE, y),
        (x + PARTICLE_SIZE, y),
        (x, y - PARTICLE_SIZE),
        (x, y + PARTICLE_SIZE),
        (x - PARTICLE_SIZE, y - PARTICLE_SIZE),
        (x - PARTICLE_SIZE, y + PARTICLE_SIZE),
        (x + PARTICLE_SIZE, y + PARTICLE_SIZE),
        (x + PARTICLE_SIZE, y - PARTICLE_SIZE),
    ]


def add_particle(x, y):
    """Attempts to add a particle at the specified location. Moves upwards if the spot is occupied."""
    # If the position is occupied, move upwards (y -= PARTICLE_SIZE) until we find an empty spot
    while is_occupied(x, y):
        y -= PARTICLE_SIZE

    particle_grid[(x, y)] = {
        'x': x,
        'y': y,
        'yvel': 0,
        'color': particle_types[active]['color'],
        'gravity': particle_types[active]['gravity'],
        'name': particle_types[active]['name']
    }
    if 'combustibility' in particle_types[active]:
        particle_grid[(x, y)]['combustibility'] = particle_types[active]['combustibility']


def add_particles_in_area(x, y):
    """Adds particles in a small area around the given position."""
    positions = [
        (i, j)
        for i in range(x - PARTICLE_SIZE * GEN_BORDER, x + PARTICLE_SIZE * (GEN_BORDER + 1), PARTICLE_SIZE)
        for j in range(y - PARTICLE_SIZE * GEN_BORDER, y + PARTICLE_SIZE * (GEN_BORDER + 1), PARTICLE_SIZE)
    ]

    for pos in positions:
        if not is_occupied(*pos):
            add_particle(*pos)


def create_screen_barrier():
    """Creates a barrier of block particles around the edges of the screen."""
    global active
    old_active = active
    active = particle_types.index(next(i for i in particle_types if i['name'] == 'block'))

    for x in range(0, WIDTH, PARTICLE_SIZE):
        # Top and Bottom Edges
        add_particle(x, 0)
        add_particle(x, HEIGHT - PARTICLE_SIZE)

    for y in range(0, HEIGHT, PARTICLE_SIZE):
        # Left and Right Edges
        add_particle(0, y)
        add_particle(WIDTH - PARTICLE_SIZE, y)

    active = old_active


def erase_particles(x, y):
    """Erases particles at the specified location (within the grid size)."""
    for i in range(x - PARTICLE_SIZE * GEN_BORDER, x + PARTICLE_SIZE * (GEN_BORDER + 1), PARTICLE_SIZE):
        for j in range(y - PARTICLE_SIZE * GEN_BORDER, y + PARTICLE_SIZE * (GEN_BORDER + 1), PARTICLE_SIZE):
            if is_occupied(i, j):
                del particle_grid[(i, j)]


def update_liquid_particle(particle, key):
    """Update behavior for liquid particles."""
    del particle_grid[key]

    if particle['name'] == 'acid':
        convert_to_acid(particle['x'], particle['y'])

    for step in range(abs(particle['yvel']) // PARTICLE_SIZE):
        new_y = particle['y'] + (PARTICLE_SIZE if particle['yvel'] > 0 else -PARTICLE_SIZE)
        if is_occupied(particle['x'], new_y):
            particle['yvel'] = 0
            break
        particle['y'] = new_y
    while is_occupied(particle['x'], particle['y']):
        particle['y'] -= PARTICLE_SIZE

    particle['yvel'] += PARTICLE_SIZE

    left = is_occupied(particle['x'] - PARTICLE_SIZE, particle['y'])
    right = is_occupied(particle['x'] + PARTICLE_SIZE, particle['y'])
    bottom = is_occupied(particle['x'], particle['y'] + PARTICLE_SIZE)
    if left and not right:
        particle['x'] += PARTICLE_SIZE
    elif right and not left:
        particle['x'] -= PARTICLE_SIZE
    elif not right and not left and bottom:
        particle['x'] += PARTICLE_SIZE * random.randint(-1, 1)

    particle_grid[(particle['x'], particle['y'])] = particle


def convert_to_fire(x, y):
    """Converts neighboring combustible particles to fire."""
    for nx, ny in get_neighbors(x, y):
        if not is_occupied(nx, ny):
            continue
        neighbor = particle_grid[(nx, ny)]
        if 'combustibility' not in neighbor:
            continue
        particle_grid[(nx, ny)] = {
            'x': nx,
            'y': ny,
            'yvel': 0,
            'color': (255, 0, 0),  # Flickering fire color
            'gravity': 'fire',
            'name': 'fire',
            'life': neighbor['combustibility'],
            'spread_timer': 3  # Initial spread timer
        }


def convert_to_acid(x, y):
    """Converts neighboring particles to acid."""
    for nx, ny in get_neighbors(x, y):
        if not is_occupied(nx, ny):
            continue
        neighbor = particle_grid[(nx, ny)]
        if 'combustibility' not in neighbor:
            continue
        particle_grid[(nx, ny)] = {
            'x': nx,
            'y': ny,
            'yvel': 0,
            'color': (0, 255, 0),
            'gravity': 'liquid',
            'name': 'acid',
        }


def update_fire_particle(particle, key):
    """Update behavior for fire particles."""
    # Remove current position
    del particle_grid[key]

    # Initialize fire properties if not already set
    if 'life' not in particle:
        particle['life'] = 20  # Lifespan of the fire
        particle['spread_timer'] = 5  # Initial spread delay
    elif particle['life'] <= 0:
        return  # Fire particle burns out

    # Decrease the spread timer
    particle['spread_timer'] -= 1

    # Spread fire to neighbors if the spread timer reaches 0
    if particle['spread_timer'] == 0:
        convert_to_fire(particle['x'], particle['y'])
        particle['spread_timer'] = 3  # Reset the spread timer

    # Simulate fire flickering and movement
    particle['x'] += PARTICLE_SIZE * random.randint(-1, 1)  # Random horizontal movement
    particle['y'] -= PARTICLE_SIZE  # Fire rises

    # Adjust position if colliding with another particle
    while is_occupied(particle['x'], particle['y']):
        if particle_grid[(particle['x'], particle['y'])]['gravity'] == 'solid':
            return
        particle['y'] += PARTICLE_SIZE

    # Decrease the fire particle's life
    particle['life'] -= 1

    # Add back to the particle grid
    particle_grid[(particle['x'], particle['y'])] = particle


def update_powder_particle(particle, key):
    """Update behavior for powder particles."""
    del particle_grid[key]

    for step in range(abs(particle['yvel']) // PARTICLE_SIZE):
        new_y = particle['y'] + (PARTICLE_SIZE if particle['yvel'] > 0 else -PARTICLE_SIZE)
        if is_occupied(particle['x'], new_y):
            particle['yvel'] = 0
            break
        particle['y'] = new_y


    particle['yvel'] += PARTICLE_SIZE
    if particle['y'] >= HEIGHT:
        particle['y'], particle['yvel'] = HEIGHT - PARTICLE_SIZE, 0
    if particle['x'] >= WIDTH:
        particle['x'] = WIDTH - PARTICLE_SIZE
    if particle['x'] < 0:
        particle['x'] = 0

    particle_grid[(particle['x'], particle['y'])] = particle


def update_gas_particle(particle, key):
    """Update behavior for gas particles to move faster and fill space efficiently."""
    del particle_grid[key]

    # Directional movement preference: upward and outward
    particle['preferred_moves'] = get_neighbors(particle['x'], particle['y'])
    random.shuffle(particle['preferred_moves'])

    # Try to move to preferred positions
    for nx, ny in particle['preferred_moves']:
        if not is_occupied(nx, ny):
            particle['x'], particle['y'] = nx, ny
            break

    # Re-add the particle to the grid
    particle_grid[(particle['x'], particle['y'])] = particle


def update_gen_particle(particle, key):
    """Generate particles from a generator."""
    global active

    if 'generating' in particle:
        old_active = active
        active = particle_types.index(next(i for i in particle_types if i['name'] == particle['generating']))
        add_particle(particle['x'], particle['y'])
        active = old_active
        return

    del particle_grid[key]

    for nx, ny in get_neighbors(*key):
        if is_occupied(nx, ny) and particle_grid[(nx, ny)]['name'] != 'generator' and particle_grid[(nx, ny)]['gravity'] != 'solid':
            particle['generating'] = particle_grid[(nx, ny)]['name']

    particle_grid[(particle['x'], particle['y'])] = particle


def update_particles():
    """Updates all particles in the particle grid."""
    for key, particle in list(particle_grid.items()):
        if particle['gravity'] == 'liquid':
            update_liquid_particle(particle, key)
        elif particle['gravity'] == 'fire':
            update_fire_particle(particle, key)
        elif particle['gravity'] == 'powder':
            update_powder_particle(particle, key)
        elif particle['gravity'] == 'gas':
            update_gas_particle(particle, key)
        elif particle['gravity'] == 'gen':
            update_gen_particle(particle, key)

        pygame.draw.rect(screen, particle['color'], (particle['x'], particle['y'], PARTICLE_SIZE, PARTICLE_SIZE))


create_screen_barrier()
while True:
    handle_events()
    apply_mouse_interaction()
    screen.fill((0, 0, 0))
    update_particles()
    draw_ui()
    pygame.display.update()

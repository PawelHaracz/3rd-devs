You are an AI assistant controlling a warehouse robot. Your task is to navigate the robot from start to finish while strictly avoiding all walls.

<objective> Warehouse grid: 4x6 (columns A-F x rows 1-4) Start position (A4): The robot starts at the bottom-left corner. Goal position (F4): The goal is at the bottom-right corner.
Walls (MUST be avoided):

B1
B3
B4
D2
D3
Allowed moves: UP, RIGHT, DOWN, LEFT

CRITICAL MOVEMENT RULES:

RIGHT: Move to the next letter in the alphabet (e.g., A to B, B to C)
LEFT: Move to the previous letter in the alphabet (e.g., B to A, C to B)
UP: Increase the number (e.g., 1 to 2, 2 to 3)
DOWN: Decrease the number (e.g., 3 to 2, 2 to 1)
Examples:

From A1, RIGHT leads to B1
From C2, UP leads to C3
From E3, LEFT leads to D3
From D4, DOWN leads to D3 </objective>
<rules> 1. Analyze the entire warehouse layout BEFORE planning the route. 2. NEVER move into or through a wall - it will damage the robot. 3. Use ONLY UP, RIGHT, DOWN, LEFT as moves. 4. Separate moves with commas in the "steps" string. 5. Provide a detailed explanation in "_thoughts", including: a) Analysis of the entire warehouse layout b) Consideration of possible routes c) Simulation of the best route d) Explanation of why this route was chosen e) Verification that the route avoids all walls 6. Output format: <RESULT> { "steps": "RIGHT, DOWN, LEFT, UP" } </RESULT> 7. Double-check your solution before submitting. </rules>
IMPORTANT:

The robot starts at A4 and must reach F4.
Hitting a wall will break the robot and fail the mission.
Verify that your path avoids ALL walls.
Ensure your path reaches F4.
REMEMBER: RIGHT changes the letter, UP changes the number.
First analyze and explain your thought process, THEN provide the steps.
Now, provide a comprehensive analysis of the warehouse layout and possible routes, followed by a valid solution to navigate from A4 to F4 while strictly avoiding all walls.
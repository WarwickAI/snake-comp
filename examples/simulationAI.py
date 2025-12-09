"""
Simulation-based AI that searches future game states to find safe paths to food.

Authors: DanielJamesHeywood, Freddie-Audley
"""

from collections import deque
from snake.logic import GameState, Turn, Snake

from snake.logic import DIRECTIONS
from examples.smartAI import smartAI as enemyAI


def simulationAI(state: GameState) -> Turn:
    priorityQueue = deque()

    turnCounts = {turn: 0 for turn in Turn}

    turnWhereTailIsNotReachable = None

    stateCount = 0

    for turn in Turn:

        newState = copyGameState(state)
        if not moveSnake(newState, turn):
            continue

        if newState.score <= state.score:

            newDistanceToNearestFood = getDistanceToNearestFood(newState)
            if newDistanceToNearestFood:

                insertIntoPriorityQueueForFoodFinding(
                    priorityQueue,
                    (newState, turn, 1, newDistanceToNearestFood)
                )

                turnCounts[turn] += 1
                
                stateCount += 1

        elif tailIsReachable(newState):
            return turn
            
        else:
            turnWhereTailIsNotReachable = turn

    if not any(turnCounts.values()):

        if turnWhereTailIsNotReachable:
            return turnWhereTailIsNotReachable

        return Turn.STRAIGHT

    while (
        any(turnCounts[turn] for turn in Turn if turn != turnWhereTailIsNotReachable)
        if turnWhereTailIsNotReachable else
        len([turnCount for turnCount in turnCounts.values() if turnCount != 0]) >= 2
    ) and stateCount <= 1024:

        state, turn, distance, _ = priorityQueue.popleft()

        turnCounts[turn] -= 1

        for newTurn in Turn:

            newState = copyGameState(state)
            if not moveSnake(newState, newTurn):
                continue

            if newState.score <= state.score:

                newDistanceToNearestFood = getDistanceToNearestFood(newState)
                if newDistanceToNearestFood:

                    insertIntoPriorityQueueForFoodFinding(
                        priorityQueue,
                        (newState, turn, distance + 1, newDistanceToNearestFood)
                    )

                    turnCounts[turn] += 1
                    
                    stateCount += 1

            elif tailIsReachable(newState):
                return turn
            
            else:
                turnWhereTailIsNotReachable = turn

    if turnWhereTailIsNotReachable:
        return turnWhereTailIsNotReachable

    _, turn, _, _ = priorityQueue.popleft()
    return turn


def tailIsReachable(state):

    priorityQueue = deque()
    insertIntoPriorityQueueForTailFinding(
        priorityQueue,
        (state, state.snake.body, getDistanceToNearestTarget(state, state.snake.body_set))
    )

    stateCount = 1

    while priorityQueue and stateCount <= 128:

        state, tail, _ = priorityQueue.popleft()

        for turn in Turn:

            newState = copyGameState(state)
            if not moveSnake(newState, turn):
                continue

            newTail = tail.copy()
            newTail.appendleft(state.snake.head)

            if newState.snake.head in newTail:
                return True

            newDistanceToTail = getDistanceToNearestTarget(newState, set(newTail))

            insertIntoPriorityQueueForTailFinding(
                priorityQueue,
                (newState, newTail, newDistanceToTail)
            )
            
            stateCount += 1

    return False


def getDistanceToNearestFood(state):
    return getDistanceToNearestTarget(state, state.food)


def getDistanceToNearestTarget(state, targets):

    x, y = state.snake.head

    minimumDistancesToCellsInBodies = {}

    minimumDistanceToHead = len(state.snake.body)

    if minimumDistanceToHead % 2 != 0:
        minimumDistanceToHead += 1

    for index, position in enumerate(state.snake.body):
        minimumDistancesToCellsInBodies[position] = minimumDistanceToHead - index

    for enemy in state.enemies:
        if enemy.isAlive:

            minimumDistanceToHead = len(enemy.body) + 1

            enemyX, enemyY = enemy.head
            if minimumDistanceToHead % 2 != (abs(x - enemyX) + abs(y - enemyY)) % 2:
                minimumDistanceToHead += 1

            for index, position in enumerate(enemy.body):
                minimumDistancesToCellsInBodies[position] = minimumDistanceToHead - index

    priorityQueue = deque()
    insertIntoPriorityQueueForDistanceFinding(
        priorityQueue,
        (state.snake.head, minimumDistancesToCellsInBodies[state.snake.head])
    )

    visited = {state.snake.head}

    for turn in Turn:
        xOffset, yOffset = DIRECTIONS[(state.snake.direction + turn.value) % 4]
        newX, newY = x + xOffset, y + yOffset
        if not (0 <= newX < state.width and 0 <= newY < state.height):
            continue
        newPosition = (newX, newY)
        if newPosition in state.walls:
            continue
    
        newDistance = 1

        if newPosition in minimumDistancesToCellsInBodies:
            newDistance = minimumDistancesToCellsInBodies[newPosition]

        insertIntoPriorityQueueForDistanceFinding(
            priorityQueue,
            (newPosition, newDistance)
        )

        visited.add(newPosition)

    while priorityQueue:

        position, distance = priorityQueue.popleft()

        if position in targets:
            return distance

        x, y = position
        
        for xOffset, yOffset in DIRECTIONS:
            newX, newY = x + xOffset, y + yOffset
            if not (0 <= newX < state.width and 0 <= newY < state.height):
                continue
            newPosition = (newX, newY)
            if newPosition in state.walls or newPosition in visited:
                continue

            newDistance = distance + 1

            if newPosition in minimumDistancesToCellsInBodies:
                minimumDistance = minimumDistancesToCellsInBodies[newPosition]
                if newDistance < minimumDistance:
                    newDistance = minimumDistance

            insertIntoPriorityQueueForDistanceFinding(
                priorityQueue,
                (newPosition, newDistance)
            )

            visited.add(newPosition)

    return None


def insertIntoPriorityQueueForFoodFinding(priorityQueue, newElement):

    def compare(lhs, rhs):

        _, _, lhDistance, lhDistanceToNearestFood = lhs
        lhTotalDistanceToNearestFood = lhDistance + lhDistanceToNearestFood

        _, _, rhDistance, rhDistanceToNearestFood = rhs
        rhTotalDistanceToNearestFood = rhDistance + rhDistanceToNearestFood

        if lhTotalDistanceToNearestFood != rhTotalDistanceToNearestFood:
            return -1 if lhTotalDistanceToNearestFood < rhTotalDistanceToNearestFood else 1

        return -1 if lhDistance > rhDistance else 0 if lhDistance == rhDistance else 1

    insertIntoPriorityQueue(priorityQueue, newElement, compare)


def insertIntoPriorityQueueForTailFinding(priorityQueue, newElement):

    def compare(lhs, rhs):

        _, _, lhDistanceToTail = lhs

        _, _, rhDistanceToTail = rhs

        return -1 if lhDistanceToTail < rhDistanceToTail else 0 if lhDistanceToTail == rhDistanceToTail else 1

    insertIntoPriorityQueue(priorityQueue, newElement, compare)


def insertIntoPriorityQueueForDistanceFinding(priorityQueue, newElement):

    def compare(lhs, rhs):

        _, lhDistance = lhs

        _, rhDistance = rhs

        return -1 if lhDistance < rhDistance else 0 if lhDistance == rhDistance else 1

    insertIntoPriorityQueue(priorityQueue, newElement, compare)


def insertIntoPriorityQueue(priorityQueue, newElement, compare):

    for index, element in enumerate(priorityQueue):

        if compare(newElement, element) <= 0:
            priorityQueue.insert(index, newElement)
            return

    priorityQueue.append(newElement)


def copyGameState(state):
    return GameState(
        width = state.width,
        height = state.height,
        snake = copySnake(state.snake),
        enemies = [copySnake(enemy) for enemy in state.enemies],
        food = state.food.copy(),
        walls = state.walls,
        score = state.score
    )


def copySnake(snake):
    copy = Snake(0, 0, snake.id)
    copy.score = snake.score
    copy.isAlive = snake.isAlive
    copy.body = snake.body.copy()
    copy.direction = snake.direction
    return copy


def moveSnake(state, turn):

    state.snake.isAlive = moveAnySnake(state, state.snake, turn)

    if state.snake.isAlive:

        for index in range(len(state.enemies)):
            if state.enemies[index].isAlive:
                moveEnemy(state, index, enemyAI(getEnemyGameState(state, index)))

    return state.snake.isAlive


def moveEnemy(state, enemyIndex, turn):

    enemy = state.enemies[enemyIndex]

    enemy.isAlive = moveAnySnake(state, enemy, turn)

    if not enemy.isAlive:

        for position in enemy.body:
            state.food.add(position)

    return enemy.isAlive


def moveAnySnake(state, snake, turn):

    nextHead = snake.get_next_head(turn)

    if nextHead in state.walls:
        return False

    if not (0 <= nextHead[0] < state.width and 0 <= nextHead[1] < state.height):
        return False

    if nextHead in snake.body and nextHead != snake.body[-1]:
        return False

    if snake is not state.snake and nextHead in state.snake.body:
        return False

    for enemy in state.enemies:
        if enemy.isAlive and enemy is not snake and nextHead in enemy.body:
            return False

    willEat = nextHead in state.food

    snake.move(turn, grow = willEat)

    if willEat:

        state.food.remove(nextHead)

        snake.score += 1
        if snake is state.snake:
            state.score += 1

    return True


def getEnemyGameState(state, enemyIndex):

    enemy = state.enemies[enemyIndex]

    return GameState(
        width = state.width,
        height = state.height,
        snake = enemy,
        enemies = [state.snake] + [otherEnemy for otherEnemy in state.enemies if otherEnemy is not enemy and otherEnemy.isAlive],
        food = state.food,
        walls = state.walls,
        score = enemy.score
    )
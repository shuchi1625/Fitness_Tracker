-- Create the Users table
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    weight DECIMAL
);

-- Create the Workouts table
CREATE TABLE Workouts (
    workout_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    workout_date DATE NOT NULL,
    duration_minutes INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Create the Exercises table
CREATE TABLE Exercises (
    exercise_id SERIAL PRIMARY KEY,
    workout_id INT NOT NULL,
    exercise_name VARCHAR(255) NOT NULL,
    reps INT,
    sets INT,
    weight_lifted DECIMAL,
    FOREIGN KEY (workout_id) REFERENCES Workouts(workout_id) ON DELETE CASCADE
);

-- Create the Goals table
CREATE TABLE Goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    goal_description TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Create the Friends table to handle the many-to-many relationship
CREATE TABLE Friends (
    friendship_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    CONSTRAINT unique_friendship UNIQUE (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    -- Ensure a user can't be friends with themselves
    CONSTRAINT no_self_friendship CHECK (user_id <> friend_id)
);

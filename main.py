import keyboard
import threading
import time
import pyautogui

class SwipeTyper:
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.swipe_path = []
        self.key_press_times = {}
        self.timer = None
        self.qwerty_lines = [
            set("qwertyuiop"),
            set("asdfghjkl"),
            set("zxcvbnm")
        ]
        self.last_input_time = time.time()

    def capture_key_press(self, event):
        key = event.name
        if event.event_type == 'down':
            if key == 'esc':
                print("ESC pressed, stopping capture.")
                return
            self.swipe_path.append(key)
            self.key_press_times[key] = time.time()
            self.reset_timer()
        elif event.event_type == 'up':
            self.key_press_times[key] = time.time() - self.key_press_times[key]

    def reset_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(1.5, self.process_swipe_path)
        self.timer.start()

    def process_swipe_path(self):
        swipe_word = ''.join(self.swipe_path)
        print(f"Swipe path: {swipe_word}")
        matched_word = self.find_closest_word(swipe_word)
        if matched_word == swipe_word:
            print(f"Exact match: {matched_word}")
        else:
            print(f"Matched word: {matched_word}")

        # Replace the last typed word with the predicted word
        self.replace_with_predicted_word(matched_word)

        self.swipe_path = []  # Reset swipe path after matching
        self.key_press_times = {}  # Reset key press times after matching

    def replace_with_predicted_word(self, predicted_word):
        # Simulate backspace to delete the incorrect word
        pyautogui.press('backspace', presses=10)  # Adjust the number of presses based on word length
        time.sleep(0.1)  # Short pause to ensure backspace is registered

        # Simulate typing the predicted word
        pyautogui.write(predicted_word)
        pyautogui.press('space')  # Add a space after typing the word

    def find_closest_word(self, swipe_word):
        relevant_lines = self.get_relevant_lines(swipe_word)
        checkpoints = self.find_checkpoints(swipe_word)
        relevant_keys = self.get_relevant_keys(swipe_word, checkpoints)

        best_match = None
        highest_score = float('-inf')

        for word in self.dictionary:
            if self.is_word_relevant(word, relevant_lines):
                score = self.calculate_score(relevant_keys, word)
                if score > highest_score:
                    highest_score = score
                    best_match = word

        return best_match

    def calculate_score(self, relevant_keys, word):
        if not relevant_keys or not word:
            return float('-inf')

        # Ensure the first and last characters match
        if relevant_keys[0] != word[0] or relevant_keys[-1] != word[-1]:
            return float('-inf')

        score = 0
        key_index = 0

        # Check characters in the word against ordered relevant keys
        for char in word:
            if key_index < len(relevant_keys) and char == relevant_keys[key_index]:
                score += 1
                key_index += 1
            elif char in relevant_keys:
                score += 0.5  # Partial match for unordered keys

        # Penalize for unmatched relevant keys
        unmatched_keys = len(relevant_keys) - key_index
        score -= unmatched_keys * 0.5

        # Factor in the length difference
        length_difference = abs(len(relevant_keys) - len(word))
        score -= length_difference * 0.5

        return score

    def find_checkpoints(self, swipe_word):
        checkpoints = []
        for i in range(2, len(swipe_word)):
            if swipe_word[i] == swipe_word[i - 2]:
                checkpoints.append(swipe_word[i-1])
        return checkpoints

    def get_relevant_keys(self, swipe_word, checkpoints):
        # Calculate the average key press time
        total_time = sum(self.key_press_times.values())
        average_time = total_time / len(self.key_press_times) if self.key_press_times else 0

        # Start with the first and last keys and checkpoints
        relevant_keys = [swipe_word[0]] + checkpoints + [swipe_word[-1]]

        # Add keys pressed longer than the average time, in order of appearance
        for key in self.swipe_path:
            if key in self.key_press_times and self.key_press_times[key] > average_time:
                if key not in relevant_keys:
                    relevant_keys.append(key)

        # Maintain the original order of keys as they appear in swipe_path
        ordered_relevant_keys = [key for key in self.swipe_path if key in relevant_keys]

        # Debugging output
        print(f"Relevant keys (unordered): {relevant_keys}")
        print(f"Relevant keys (ordered): {ordered_relevant_keys}")

        return ordered_relevant_keys

    def get_relevant_lines(self, swipe_word):
        relevant_lines = set()
        for char in swipe_word:
            for i, line in enumerate(self.qwerty_lines):
                if char in line:
                    relevant_lines.add(i)
                    break
        return relevant_lines

    def is_word_relevant(self, word, relevant_lines):
        for char in word:
            char_line = None
            for i, line in enumerate(self.qwerty_lines):
                if char in line:
                    char_line = i
                    break
            if char_line not in relevant_lines:
                return False
        return True

def load_dictionary(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

def main():
    dictionary = load_dictionary('dictionary.txt')  # Load your dictionary
    swipe_typer = SwipeTyper(dictionary)

    # Set up the key capture
    keyboard.hook(swipe_typer.capture_key_press)
    print("Start typing... The prediction will be shown after 1.5 seconds of inactivity.")
    keyboard.wait
# Find words that share a long prefix.

# Find words whose common prefix meets the threshold.
def similar_word(content: str, threshold: float = 0.82):

    # Validate the threshold before comparing words.
    if threshold > 0.99 or threshold < 0.1:
        raise ValueError("Use a valid threshold, a number between 0.1 and 0.99")

    word_list = []

    similarity_threshold = threshold

    similar_words = {}

    out = []

    characters_to_remove = [".", ",", ";", ":", "!", "?", "¡", "¿", "-", "_", "(", ")", "[", "]", "{", "}", "\"", "'"]

    accented_characters = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n"
    }
    
    # Normalize: lowercase, strip punctuation, remove accents.
    for word in content.split():
        word_lower = word.lower()

        # Remove specified characters from the word
        for char in characters_to_remove:
            word_lower = word_lower.replace(char, "")

        # Replace accented characters
        for accented, unaccented in accented_characters.items():
            word_lower = word_lower.replace(accented, unaccented)

        if word_lower not in word_list:
            word_list.append(word_lower)

    for word in word_list:
        

        # Compare common prefixes; skip identical words.
        comparaciones = {}

        for other_word in word_list:
            if word == other_word:
                continue

            # Calculate similarity based on character matches
            matched = 0
            for a, b in zip(word, other_word):
                if a != b:
                    break
                matched += 1

            similarity = matched / max(len(word), len(other_word))

            if similarity >= similarity_threshold:
                similar_words.setdefault(word, []).append(other_word)

            comparaciones[other_word] = similarity

        # Sort the comparisons by similarity in descending order
        sorted_comparisons = sorted(comparaciones.items(), key=lambda x: x[1], reverse=True)   

        #print(f"Word: {word}")
        #print("Comparisons:")
        #for other_word, similarity in sorted_comparisons:
        #    print(f"  {other_word}: {similarity:.2f}")

    # Collect each group once.
    map = []

    for word, similars in similar_words.items():
        
        for similar in similars:
            if similar not in map:
                map.append(similar)

        if word in map:
            continue
            
        else:
            for similar in similars:
                out.append(similar)

            out.append(word)


    return out
                

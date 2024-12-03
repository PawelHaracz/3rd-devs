initial_response = photo_query("START")
links_json_text = ask_model_to_retrieve_urls(initial_response)
links = json.loads(links_json_text)
print(json.dumps(links, indent=2, ensure_ascii=False))
# links = [link.replace('.PNG', '-small.PNG') for link in links]
filenames = store_photos(links)
final_photos = []
while len(filenames) > 0:
    print("There are still photos to process: " + str(filenames))
    image_name = filenames.pop()
    command = ask_model_for_corrections(os.path.join(TMP_DIR, image_name), image_name).strip()
    if command == 'STORE':
        print("Photo OK: " + image_name)
        final_photos.append(image_name)
        continue
    elif command == 'DROP':
        print("Dropping photo: " + image_name)
        continue
    elif command in ['REPAIR', 'BRIGHTEN', 'DARKEN']:
        result = photo_query(f"{command} {image_name}")
        found = re.findall(r'(IMG_.*PNG)', result)
        print(found)
        for new_photo_name in found:
            # Possible improvement: This should be extracted by LLM, not by regexp... But I don't have time for this.
            new_photo_url = f"https://centrala.ag3nts.org/dane/barbara/{new_photo_name}"
            store_photo(new_photo_url)
            filenames.append(new_photo_name)
print("End of photos preparation")

print("Stored photos:" + str(final_photos))

final_photo_paths = [os.path.join(TMP_DIR, image_name) for image_name in final_photos]

description = ask_model_for_description(final_photo_paths)
print(description)

# Possible improvement: Loop and add hints to prompt dynamically
task_api.send_task("photos", description)
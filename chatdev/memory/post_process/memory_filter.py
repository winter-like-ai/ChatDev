import json  
import os
import argparse
filter_threshold = 0.9

def filter_valuegain(directory, filtered_directory): 
    """根据经验块的价值增益（valueGain）执行记忆过滤，删除 valueGain 小于过滤阈值（filter_threshold）的经验。

    参数 (Keyword arguments):
    directory -- 输入的 memoryCards 目录, 形如 "./ecl/memory/MemoryCards.json"
    filtered_directory -- 过滤后输出保留的 memoryCards 目录, 形如 "./ecl/memory/MemoryCards.json"
    """
    with open(directory) as file:
        content = json.load(file)
        new_content = []
        for memorypiece in content:
            experiences = memorypiece.get("experiences")
            filtered_experienceList = []
            
            if experiences != None:
                print("origin:",len(experiences))
                for experience in experiences:
                    valueGain = experience.get("valueGain")
                    print(valueGain)
                    if valueGain >= filter_threshold:
                        filtered_experienceList.append(experience)
                print(len(experiences))
                memorypiece["experiences"] = filtered_experienceList
                new_content.append(memorypiece)
            else:
                new_content.append(memorypiece)
        file.close()
    with open(filtered_directory, 'w') as file:
        json.dump(content, file)
        file.close()


def main():
    parser = argparse.ArgumentParser(description="Process some directories.")
    parser.add_argument("threshold", type=float, help="The filtered threshold for experiences")
    parser.add_argument("directory", type = str, help="The directory to process")
    parser.add_argument("filtered_directory", type= str, help="The directory for output")


    args = parser.parse_args()
    filter_threshold = args.threshold 
    filter_valuegain(args.directory, args.filtered_directory)

if __name__ == "__main__":
    main()
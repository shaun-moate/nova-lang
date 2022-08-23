package main

import (
	"bufio"
	"strings"
	"os"
	"fmt"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func open_file(program_file_path string) (fp *os.File) {
	fp, err := os.Open(program_file_path)
	check(err)
	return fp
}

func read_lines(raw_file *os.File) []string {
	var comment string = "//"
	var lines []string
	scanner := bufio.NewScanner(raw_file)
	for scanner.Scan() {
		var row int = 0
		var line string = scanner.Text()
		split := strings.Split(line, comment)
		lines = append(lines, split[0])
		row += 1
	}
	return lines
}

// TODO: add read words -> iterate through read_lines and collect word, location (file_path, row, col)
func get_word_indices(lines []string) [][]int {
	words := make([][]int, 0)
	for i := 0; i < len(lines); i++ {
		indices := make([]int, 0)
		if len(lines[i]) > 0 {
			var index int = 0
			for {
				next := strings.Index(lines[i][index:], " ")
				indices = append(indices, index)
				if next > 0 {
					index += next+1
				} else {
					break
				}
			}
		} else if len(lines[i]) == 0 {
			indices = append(indices, []int{-1}...)
		}
		words = append(words, [][]int{indices}...)
	}
	return words
}

func main() {
	var file_path string = os.Args[1]
	var file *os.File = open_file(file_path)
	var lines []string = read_lines(file)
	fmt.Println(get_word_indices(lines))
}

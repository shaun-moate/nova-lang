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

func get_word_indices(lines []string) [][]int {
	windices := make([][]int, 0)
	for i := 0; i < len(lines); i++ {
		indices := make([]int, 0)
		if len(lines[i]) > 0 {
			indices = find_word_indices(lines[i])
		} else if len(lines[i]) == 0 {
			indices = append(indices, []int{-1}...)
		}
		windices = append(windices, [][]int{indices}...)
	}
	return windices
}

func find_word_indices(line string) []int {
	var index int = find_first_index(line)
	var indices []int
	for {
		next := strings.Index(line[index:], " ")
		indices = append(indices, index)
		if next > 0 {
			index += next+1
		} else {
			break
		}
	}
	return indices
}

func find_first_index(line string) int {
	var index int
	index = len(line) - len(strings.TrimLeft(line, " "))
	return index
}

type Location struct {
	file_path     string
	row           int
	col           int
}

func generate_word_locations(file_path string) []Location {
	var file *os.File = open_file(file_path)
	var lines []string = read_lines(file)
	var indices [][]int = get_word_indices(lines)
	var locations []Location

	for i := 0; i < len(indices); i++ {
		if indices[i][0] >= 0 {
			for j := 0; j < len(indices[i]); j++ {
				l := Location {
						file_path: file_path,
						row: i+1,
						col: indices[i][j],
					}
				locations = append(locations, l)
			}
		}
	}
	return locations
}

// TODO: create a parse_words, combining read_lines and get_word_indices to create 2d array of words
// TODO: implement tokenisation of words -> convert words into token with actions

func main() {
	var file_path string = os.Args[1]
	var locations []Location = generate_word_locations(file_path)
	fmt.Println(locations)
}

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
		var line string = scanner.Text()
		split := strings.Split(line, comment)
		lines = append(lines, split[0])
	}
	return lines
}

// TODO: add read words -> iterate through read_lines and collect word, location (file_path, row, col)

func main() {
	var file *os.File = open_file("tests/arithmetic-plus.nv")
	var lines []string = read_lines(file)
	fmt.Println(lines[1])
}

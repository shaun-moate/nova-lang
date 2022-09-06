package main

import (
	"os"
	"fmt"
	"bufio"
	"strings"
	"strconv"
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

func generate_word_indices(lines []string) [][]int {
	windices := make([][]int, 0)
	for i := 0; i < len(lines); i++ {
		indices := make([]int, 0)
		if len(lines[i]) > 0 {
			indices = find_word_indices_for_line(lines[i])
		} else if len(lines[i]) == 0 {
			indices = append(indices, []int{-1}...)
		}
		windices = append(windices, [][]int{indices}...)
	}
	return windices
}

func find_word_indices_for_line(line string) []int {
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
	filePath      string
	row           int
	col           int
}

type Word struct {
	word          string
	location      Location
}

func generate_words(file_path string) []Word {
	var file *os.File = open_file(file_path)
	var lines []string = read_lines(file)
	var indices [][]int = generate_word_indices(lines)
	var words []Word

	for i := 0; i < len(indices); i++ {
		if indices[i][0] >= 0 {
			for j := 0; j < len(indices[i]); j++ {
				var row int = i
				var start int = indices[i][j]
				var end int = 0
				if j+1 > len(indices[i])-1 {
					end = len(lines[i])+1
				} else {
					end = indices[i][j+1]
				}
				l := Word {
						word: lines[row][start:end-1],
						location: Location {
							filePath: file_path,
							row: row+1,
							col: start+1,
						},
					}
				words = append(words, l)
			}
		}
	}
	return words
}

type Token struct {
	tokenId     int
	token       interface{}
	location    Location
}

const (
	TOKEN_INT int = iota
	TOKEN_OP
	TOKEN_COUNT
)

func test_tokens(length int, f string) {
	if TOKEN_COUNT != length {
		fmt.Printf("ERROR: ensure all tokens accounted for in %s", f)
		os.Exit(1)
	}
}

func generate_tokens(words []Word) []Token {
	test_tokens(2, "generate_tokens()")
	var tokens []Token
	for j := 0; j < len(words); j++ {
		token_i, err := strconv.Atoi(words[j].word)
		if err == nil {
			var token Token = Token {
				tokenId: TOKEN_INT,
				token: token_i,
				location: words[j].location,
			}
			tokens = append(tokens, token)
		} else {
			var token Token = Token {
				tokenId: TOKEN_OP,
				token: words[j].word,
				location: words[j].location,
			}
			tokens = append(tokens, token)
		}
	}
	return tokens
}


type Operand struct {
	operandId   int
	tokenId     int
	token       interface{} // TODO: turn this into a Union type with set types
	location    Location
}

const (
	OP_PUSH_INT int = iota
	OP_PLUS
	OP_DUMP
	OP_COUNT
)

func generate_operands() map[string]int {
	test_ops(3, "generate_operands()")
	return map[string]int{
		"+": OP_PLUS,
		"dump": OP_DUMP,
	}
}

func test_ops(length int, f string) {
	if OP_COUNT != length {
		fmt.Printf("ERROR: ensure all operands accounted for in %s", f)
		os.Exit(1)
	}
}

func generate_program(tokens []Token) []Operand {
	var mapOperands map[string]int = generate_operands()
	var program []Operand
	for j := 0; j < len(tokens); j++ {
		if tokens[j].tokenId == TOKEN_OP {
			if _, ok := mapOperands[tokens[j].token.(string)]; ok {
				var operand Operand = Operand {
					operandId: mapOperands[tokens[j].token.(string)],
					tokenId: TOKEN_INT,
					token: tokens[j].token,
					location: tokens[j].location,
				}
				program = append(program, operand)
			} else {
				f := tokens[j].location.filePath
				r := tokens[j].location.row
				c := tokens[j].location.col
				o := tokens[j].token.(string)
				fmt.Printf("%s:%d:%d: ERROR: unknown operand `%s`", f, r, c, o)
				os.Exit(1)
			}
		} else if tokens[j].tokenId == TOKEN_INT {
			var operand Operand = Operand {
				operandId: OP_PUSH_INT,
				tokenId: TOKEN_OP,
				token: tokens[j].token,
				location: tokens[j].location,
			}
			program = append(program, operand)
		}
	}
	return program
}

type Stack struct {
	items     []int
}

func NewEmptyStack() *Stack {
	return &Stack {
		items: nil,
	}
}

func (s *Stack) Push(v int) {
	s.items = append(s.items, v)
}

func (s *Stack) Pop() int {
	var l int = len(s.items)
	if l == 0 {
		return 0
	}
	lastItem := s.items[l-1]
	s.items = s.items[:l-1]
	return lastItem
}

func simulate_program(program []Operand) {
	stack := NewEmptyStack()
	for i := 0; i < len(program); i++ {
		if program[i].operandId == OP_PUSH_INT {
			stack.Push(program[i].token.(int))
		} else if program[i].operandId == OP_PLUS {
			x := stack.Pop()
			y := stack.Pop()
			stack.Push(x+y)
		} else if program[i].operandId == OP_DUMP {
			x := stack.Pop()
			fmt.Printf("%d", x)
		} else {
			fmt.Printf("ERROR: ensure all operands is unreachable in simulate_program()")
			os.Exit(1)
		}
	}
}

func program_helper() {
    fmt.Printf("-------------------------------------------\n")
    fmt.Printf("Usage: nova-lang <SUBCOMMAND> [ARGS]\n")
    fmt.Printf("SUBCOMMANDS:\n")
    fmt.Printf("    --help     (-h)              Present the helper documents\n")
    fmt.Printf("    --simulate (-s) <file>       Simulate the program using go-lang\n")
    fmt.Printf("-------------------------------------------\n")
	os.Exit(0)
}

// TODO: implement compile_program()
// TODO: implement testing framework
// TODO: replicate operands to pass all tests on both simulation and compilation
// TODO: consider structuring the project to include class folder, placing the Parser() in it <- create a parser object to action the parsing of the file

func main() {
	var runtime string = os.Args[1]
	var file_path string = os.Args[2]
	var words []Word = generate_words(file_path)
	var tokens []Token = generate_tokens(words)
	var program []Operand = generate_program(tokens)
	if runtime == "-s" || runtime == "--simulate" {
		simulate_program(program)
	} else if runtime == "-h" || runtime == "--help" {
		program_helper()
	} else {
		program_helper()
	}
}

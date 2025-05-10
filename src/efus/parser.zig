pub const Efus = struct {
    instructions: []const Instruction,
    allocator: Allocator,

    pub fn eval(self: *Efus, names: Namespace) !EObject {
        for (self.instructions) |instr| {
            try instr.evaluate(null, names);
        }
    }
};

pub const Parser = struct {
    index: u32,
    text: []const u8,
    allocator: Allocator,

    pub fn init(allocator: Allocator, text: []const u8) Parser {
        return .{
            .allocator = allocator,
            .index = 0,
            .text = text,
        };
    }

    pub fn isSymbol(c: u8) bool {
        return 'A' <= c and c <= 'z';
    }
    pub fn isSpace(c: u8) bool {
        return c == ' ' or c == '\t';
    }
    pub fn parse_symbol(self: *Parser) !?[]const u8 {
        const start = self.index;
        while (Parser.isSymbol(self.char())) {
            self.next_inline() catch break;
        }
        return self.slicednbefore(start);
    }
    pub fn slicednbefore(self: *Parser, start: u32) ?[]const u8 {
        if (start != self.index) {
            return self.text[start..self.index];
        } else {
            return null;
        }
    }
    pub fn next_inline(self: *Parser) !void {
        self.index += 1;
        if (self.index >= self.text.len) {
            return EfusError.EndOfFile;
        } else if (self.char() == '\n') {
            return EfusError.EndOfLine;
        }
    }
    pub fn parse_compcall(self: *Parser) !?InstantiateComponent {
        if (try self.parse_symbol()) |templname| {
            if (self.eol()) {
                return InstantiateComponent.init(
                    self.allocator,
                    templname,
                    null,
                    null,
                );
            }
            const alias = try self.parse_compcallalias();
            if (self.eol()) {
                return InstantiateComponent.init(
                    self.allocator,
                    templname,
                    alias,
                    null,
                );
            }
            const arguments = try self.parse_compcallargs();
            if (!self.eol()) {
                return EfusError.ExtraTokensAfterArguments;
            }
            return InstantiateComponent.init(
                self.allocator,
                templname,
                alias,
                arguments,
            );
        }
        return null;
    }
    fn parse_compcallargs(self: *Parser) !EArguments {
        var args = EArguments.init(self.allocator);
        while (true) {}
    }
    fn parse_next_key_eq_val(self: *Parser) !st {
        self.skip_inline_spaces();
    }
    fn skip_inline_spaces(self: *Parser) !u8 {
        const start = self.index;
        while (Parser.isSpace(self.char())) {
            try self.next_inline();
        }
        return self.index - start;
    }
    fn parse_compcallalias(self: *Parser) !?[]const u8 {
        if (self.eol()) {
            return EfusError.EndOfLine;
        }
        if (self.char() == '&') {
            try self.next_inline();
            return try self.parse_symbol();
        } else {
            return null;
        }
    }
    fn char(self: *Parser) u8 {
        return self.text[self.index];
    }
    fn eol(self: *Parser) bool {
        const start = self.index;
        while (true) {
            if (self.index >= self.text.len) {
                return true;
            } else if (self.char() == '\n') {
                return true;
            } else if (Parser.isSpace(self.char())) {
                self.index += 1;
            } else {
                self.index = start;
                return false;
            }
        }
    }
};

const std = @import("std");
const Allocator = std.mem.Allocator;

const instruction = @import("instruction.zig");
const Instruction = instruction.Instruction;
const InstantiateComponent = instruction.InstantiateComponent;

const namespace = @import("namespace");
const Namespace = namespace.Namespace;

const objs = @import("objects.zig");
const EObject = objs.EObject;
const EfusError = @import("errors.zig").EfusError;

const attributemanager = @import("attributemanager.zig");
const EArguments = attributemanager.EArguments;

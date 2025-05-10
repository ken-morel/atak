pub const EType = enum {
    String,
    Integer,
    Float,
    Boolean,
    Rien,
};

pub const EValue = union(enum) {
    String: []const u8,
    Integer: i64,
    Float: f64,
    Boolean: bool,
    Rien,
};

pub const EObject = struct {
    value: EValue,
    type: EType,
    pub fn isType(self: EObject, t: EType) bool {
        return t == self.type;
    }
};

#pragma once

#include <cstdint>


template<uint32_t addr, uint32_t mask, uint32_t offset, class rw_policy>
struct reg_t
{
    static void write(uint32_t val)
    {
        rw_policy::write(reinterpret_cast<volatile uint32_t *>(addr),
                            mask,
                         offset,
                            val);
    }
    
    static uint32_t read()
    {
        return rw_policy::read(reinterpret_cast<volatile uint32_t *>(addr),
                            mask,
                         offset);
    }
};

struct rw_t
{
    static void write(volatile uint32_t *addr, uint32_t mask, uint32_t offset, uint32_t val)
    {
        *addr = (*addr & ~(mask << offset)) | ((val & mask) << offset);
    }
    static uint32_t read(volatile uint32_t *addr, uint32_t mask, uint32_t offset)
    {
        return (*addr >> offset) & mask;
    }
};

struct wo_t
{
    static void write(volatile uint32_t *addr, uint32_t mask, uint32_t offset, uint32_t val)
    {
        *addr = (*addr & ~(mask << offset)) | ((val & mask) << offset);
    }
};

struct ro_t
{
    static uint32_t read(volatile uint32_t *addr, uint32_t mask, uint32_t offset)
    {
        return (*addr >> offset) & mask;
    }
};

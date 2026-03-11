#!/usr/bin/env python3
"""
txt_to_fasta.py - Convert plain text sequence files to FASTA format.

This script reads sequences from a text file (one sequence per line) and
converts them to FASTA format with auto-generated headers. It validates
sequences based on the specified type (DNA or protein) and skips invalid lines.

Usage:
    python txt_to_fasta.py --input sequences.txt --output output.fasta --type dna

Author: Generated for bioinformatics workflows
"""

import argparse
import sys
from pathlib import Path


# Valid characters for each sequence type
VALID_DNA_CHARS = set("ATCGNatcgn")
VALID_PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYacdefghiklmnpqrstvwy*-XBZxbz")


def validate_sequence(sequence: str, seq_type: str) -> bool:
    """
    Validate a sequence based on its type.

    Args:
        sequence: The sequence string to validate.
        seq_type: Either 'dna' or 'protein'.

    Returns:
        True if the sequence contains only valid characters, False otherwise.
    """
    if not sequence:
        return False

    valid_chars = VALID_DNA_CHARS if seq_type == "dna" else VALID_PROTEIN_CHARS
    return all(char in valid_chars for char in sequence)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Namespace object containing parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert plain text sequence files to FASTA format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python txt_to_fasta.py --input sequences.txt --output output.fasta --type dna
    python txt_to_fasta.py -i proteins.txt -o proteins.fasta -t protein
        """,
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Path to input text file (one sequence per line)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Path to output FASTA file"
    )

    parser.add_argument(
        "-t", "--type",
        type=str,
        choices=["dna", "protein"],
        required=True,
        help="Sequence type for validation: 'dna' (A,T,C,G,N) or 'protein' (standard amino acids)"
    )

    return parser.parse_args()


def convert_txt_to_fasta(input_path: str, output_path: str, seq_type: str) -> dict:
    """
    Convert a text file with sequences to FASTA format.

    Args:
        input_path: Path to the input text file.
        output_path: Path to the output FASTA file.
        seq_type: Sequence type ('dna' or 'protein') for validation.

    Returns:
        Dictionary with conversion statistics (total, valid, invalid counts).

    Raises:
        FileNotFoundError: If the input file does not exist.
        PermissionError: If unable to read input or write output file.
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    stats = {"total": 0, "valid": 0, "invalid": 0, "skipped_lines": []}

    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        sequence_number = 0

        for line_number, line in enumerate(infile, start=1):
            # Strip whitespace and skip empty lines
            sequence = line.strip()

            if not sequence:
                continue

            stats["total"] += 1

            # Validate the sequence
            if validate_sequence(sequence, seq_type):
                sequence_number += 1
                stats["valid"] += 1

                # Write FASTA header and sequence
                outfile.write(f">sequence_{sequence_number}\n")

                # Write sequence in standard FASTA line length (80 characters)
                for i in range(0, len(sequence), 80):
                    outfile.write(f"{sequence[i:i+80].upper()}\n")
            else:
                stats["invalid"] += 1
                stats["skipped_lines"].append(line_number)

    return stats


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_arguments()

    print(f"Converting {args.input} to FASTA format...")
    print(f"Sequence type: {args.type}")

    try:
        stats = convert_txt_to_fasta(args.input, args.output, args.type)

        # Print summary
        print(f"\nConversion complete!")
        print(f"  Total sequences processed: {stats['total']}")
        print(f"  Valid sequences written:   {stats['valid']}")
        print(f"  Invalid sequences skipped: {stats['invalid']}")

        if stats["skipped_lines"]:
            # Show first few skipped lines if there are many
            if len(stats["skipped_lines"]) <= 10:
                lines_str = ", ".join(map(str, stats["skipped_lines"]))
            else:
                lines_str = ", ".join(map(str, stats["skipped_lines"][:10])) + "..."
            print(f"  Skipped line numbers: {lines_str}")

        print(f"\nOutput written to: {args.output}")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

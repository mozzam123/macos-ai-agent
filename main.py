from app.tools.macos import open_application


def main():
    result = open_application("Finder")
    print(result)


if __name__ == "__main__":
    main()
